import datetime, re, time;
from cBugReport import cBugReport;
from cDebuggerExtension import cDebuggerExtension;
from daxExceptionHandling import daxExceptionHandling;
from dxConfig import dxConfig;
from cCdbWrapper_fbDetectAndReportVerifierErrors import cCdbWrapper_fbDetectAndReportVerifierErrors;
from NTSTATUS import *;

def fnGetDebuggerTime(sDebuggerTime):
  # Parse .time and .lastevent timestamps; return a number of seconds since an arbitrary but constant starting point in time.
  sMonths = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec";
  oTimeMatch = re.match("^%s$" % r"\s+".join([
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)",                        # Weekday
    r"(%s)" % sMonths,                                       # Month
    r"(\d+)",                                                # Day in month
    r"(\d+):(\d+):(\d+).(\d+)",                              # Hour:Minute:Second.Milisecond
    r"(\d+)",                                                # Year
    r"\(.*\)",                                               # (Timezone)
  ]), sDebuggerTime);
  assert oTimeMatch, "Cannot parse debugger time: %s" % repr(sDebuggerTime);
  sWeekDay, sMonth, sDay, sHour, sMinute, sSecond, sMilisecond, sYear = oTimeMatch.groups();
  oDateTime = datetime.datetime(
    long(sYear),
    sMonths.find(sMonth) / 4 + 1,
    long(sDay),
    long(sHour),
    long(sMinute),
    long(sSecond),
    long(sMilisecond.ljust(6, "0")),
  );
  return (oDateTime - datetime.datetime(1976,8,28)).total_seconds();

def cCdbWrapper_fCdbStdInOutThread(oCdbWrapper):
  # cCdbWrapper initialization code already acquire a lock on cdb on behalf of this thread, so the "interrupt on
  # timeout" thread does not attempt to interrupt cdb while this thread is getting started.
  try:
    # There are situations where an exception should be handled by the debugger and not by the application, this
    # boolean is set to True to indicate this and is used to execute either "gh" or "gn" in cdb.
    bPassLastExceptionToApplication = False;
    # Sometime an event can trigger multiple exceptions but only the first one contains new information. For instance
    # when a new process is created, up to three exceptions can happen that are related this this event. In such cases
    # BugId may need to ignore all but the first such exception. to be able to ignore exceptions, a dict contains the
    # exception code of the exception to ignore for each process.
    duIgnoreNextExceptionCode_by_uProcessId = {};
    # Create a list of commands to set up event handling. The default for any exception not explicitly mentioned is to
    # be handled as a second chance exception.
    asExceptionHandlingCommands = ["sxd *"];
    # request second chance debugger break for certain exceptions that indicate the application has a bug.
    for sCommand, axExceptions in daxExceptionHandling.items():
      for xException in axExceptions:
        sException = isinstance(xException, str) and xException or ("0x%08X" % xException);
        asExceptionHandlingCommands.append("%s %s" % (sCommand, sException));
    sExceptionHandlingCommands = ";".join(asExceptionHandlingCommands);
    
    # Read the initial cdb output related to starting/attaching to the first process.
    asIntialCdbOutput = oCdbWrapper.fasReadOutput();
    if not oCdbWrapper.bCdbRunning: return;
    # Turn off prompt information as it is not useful most of the time, but can clutter output.
    oCdbWrapper.fasSendCommandAndReadOutput(
        ".prompt_allow -dis -ea -reg -src -sym; $$ Set up the cdb prompt to be very minimal");
    if not oCdbWrapper.bCdbRunning: return;
    oCdbWrapper.oExtension = cDebuggerExtension.foLoad(oCdbWrapper);
    if not oCdbWrapper.bCdbRunning: return;
    
    # Exception handlers need to be set up.
    oCdbWrapper.bExceptionHandlersHaveBeenSet = False;
    # Only fire fApplicationRunningCallback if the application was started for the first time or resumed after it was
    # paused to analyze an exception. 
    bApplicationRunningCallbackFired = False;
    bDebuggerNeedsToResumeAttachedProcesses = len(oCdbWrapper.auProcessIdsPendingAttach) > 0;
    # An bug report will be created when needed; it is returned at the end
    oBugReport = None;
    # Memory can be allocated to be freed later in case the system has run low on memory when an analysis needs to be
    # performed. This is done only if dxConfig["uReserveRAM"] > 0. The memory is allocated at the start of
    # debugging, freed right before an analysis is performed and reallocated if the exception was not fatal.
    bReserveRAMAllocated = False;
    while oCdbWrapper.bCdbRunning and (
      asIntialCdbOutput # We still need to process the initial cdb output
      or len(oCdbWrapper.auProcessIdsPendingAttach) > 0 # We still need to attach to more processes
      or not oCdbWrapper.bApplicationTerminated # There are still processes running.
    ):
      # If requested, reserve some memory in cdb that can be released later to make analysis under low memory conditions
      # more likely to succeed.
      if dxConfig["uReserveRAM"] and not bReserveRAMAllocated:
        uBitMask = 2 ** 31;
        while uBitMask >= 1:
          sBit = dxConfig["uReserveRAM"] & uBitMask and "A" or "";
          if bReserveRAMAllocated:
            oCdbWrapper.fasSendCommandAndReadOutput("aS /c RAM .printf \"${RAM}{$RAM}%s\"; $$ Allocate RAM" % sBit);
          elif sBit:
            oCdbWrapper.fasSendCommandAndReadOutput("aS RAM \"%s\"; $$ Allocate RAM" % sBit);
            bReserveRAMAllocated = True;
          if not oCdbWrapper.bCdbRunning: return;
          uBitMask /= 2;
      # Discard any cached information about modules loaded in the current process, as this may be about to change
      # during execution of the application.
      oCdbWrapper.doModules_by_sCdbId = None;
      if asIntialCdbOutput:
        # First parse the intial output
        asCdbOutput = asIntialCdbOutput;
        asIntialCdbOutput = None;
      else:
        # cdb will no longer have a "current process", as the application will be running.
        if oCdbWrapper.oCurrentProcess:
          # If we were expecting any exceptions, they should have been triggered by now.
          if oCdbWrapper.oCurrentProcess.uId in duIgnoreNextExceptionCode_by_uProcessId:
            del duIgnoreNextExceptionCode_by_uProcessId[oCdbWrapper.oCurrentProcess.uId];
          # The process is no longer new
          oCdbWrapper.oCurrentProcess.bNew = False;
          oCdbWrapper.oCurrentProcess = None;
        # All processes that were terminated should be removed from the list of known processes:
        while oCdbWrapper.auProcessIdsPendingDelete:
          del oCdbWrapper.doProcess_by_uId[oCdbWrapper.auProcessIdsPendingDelete.pop()];
        # Then attach to a process, or start or resume the application
        if len(oCdbWrapper.auProcessIdsPendingAttach) == 0:
          # Report that the application is about to start running or be resumed.
          if not bApplicationRunningCallbackFired:
            if oCdbWrapper.fApplicationRunningCallback:
              oCdbWrapper.fApplicationRunningCallback();
            bApplicationRunningCallbackFired = True;
          else:
            if oCdbWrapper.fApplicationResumedCallback:
              oCdbWrapper.fApplicationResumedCallback();
        # Mark the time when the application was resumed.
        asCdbTimeOutput = oCdbWrapper.fasSendCommandAndReadOutput(".time; $$ Get debugger time");
        if not oCdbWrapper.bCdbRunning: return;
        oTimeMatch = len(asCdbTimeOutput) > 0 and re.match(r"^Debug session time: (.*?)\s*$", asCdbTimeOutput[0]);
        assert oTimeMatch, "Failed to get debugger time!\r\n%s" % "\r\n".join(asCdbTimeOutput);
        del asCdbTimeOutput;
        oCdbWrapper.oApplicationTimeLock.acquire();
        try:
          oCdbWrapper.nApplicationResumeDebuggerTime = fnGetDebuggerTime(oTimeMatch.group(1));
          oCdbWrapper.nApplicationResumeTime = time.clock();
        finally:
          oCdbWrapper.oApplicationTimeLock.release();
        # Release the lock on cdb so the "interrupt on timeout" thread can attempt to interrupt cdb while the
        # application is running.
        if len(oCdbWrapper.auProcessIdsPendingAttach) == 0:
          oCdbWrapper.oCdbLock.release();
        try:
          asCdbOutput = oCdbWrapper.fasSendCommandAndReadOutput(
            "g%s; $$ Run application" % (bPassLastExceptionToApplication and "n" or "h"),
            bShowOnlyCommandOutput = True,
            bOutputIsInformative = True,
            bOutputCanContainApplicationOutput = True,
          );
          if not oCdbWrapper.bCdbRunning: return;
        finally:
          # Get a lock on cdb so the "interrupt on timeout" thread does not attempt to interrupt cdb while we execute
          # commands.
          if len(oCdbWrapper.auProcessIdsPendingAttach) == 0:
            oCdbWrapper.oCdbLock.acquire();
        # If the application was not suspended on purpose to attach to another process, report it:
        if len(oCdbWrapper.auProcessIdsPendingAttach) == 0 and oCdbWrapper.fApplicationSuspendedCallback:
          oCdbWrapper.fApplicationSuspendedCallback();
      # Find out what event caused the debugger break
      asLastEventOutput = oCdbWrapper.fasSendCommandAndReadOutput(".lastevent; $$ Get information about last event",
        bOutputIsInformative = True,
      );
      if not oCdbWrapper.bCdbRunning: return;
      # Sample output:
      # |Last event: 3d8.1348: Create process 3:3d8                
      # |  debugger time: Tue Aug 25 00:06:07.311 2015 (UTC + 2:00)
      # - or -
      # |Last event: c74.10e8: Exit process 4:c74, code 0          
      # |  debugger time: Tue Aug 25 00:06:07.311 2015 (UTC + 2:00)
      if (len(asLastEventOutput) > 0 and asLastEventOutput[0] == ""):
        # Sometimes, for unknown reasons, output can start with a blank line: remove it.
        asLastEventOutput.pop(0);
      assert len(asLastEventOutput) == 2, "Invalid .lastevent output:\r\n%s" % "\r\n".join(asLastEventOutput);
      oEventMatch = re.match(
        "^%s\s*$" % "".join([
          r"Last event: ([0-9a-f]+)\.[0-9a-f]+: ",
          r"(?:",
            r"(Create|Exit) process [0-9a-f]+\:([0-9a-f]+)(?:, code [0-9a-f]+)?",
          r"|",
            r"(.*?) \- code ([0-9a-f]+) \(!*\s*(first|second) chance\s*!*\)",
          r"|",
            r"Hit breakpoint (\d+)",
          r")",
        ]),
        asLastEventOutput[0],
        re.I
      );
      assert oEventMatch, "Invalid .lastevent output on line #1:\r\n%s" % "\r\n".join(asLastEventOutput);
      oEventTimeMatch = re.match(r"^\s*debugger time: (.*?)\s*$", asLastEventOutput[1]);
      assert oEventTimeMatch, "Invalid .lastevent output on line #2:\r\n%s" % "\r\n".join(asLastEventOutput);
      oCdbWrapper.oApplicationTimeLock.acquire();
      try:
        if oCdbWrapper.nApplicationResumeDebuggerTime:
          # Add the time between when the application was resumed and when the event happened to the total application
          # run time.
          oCdbWrapper.nApplicationRunTime += fnGetDebuggerTime(oEventTimeMatch.group(1)) - oCdbWrapper.nApplicationResumeDebuggerTime;
        # Mark the application as suspended by setting nApplicationResumeDebuggerTime to None.
        oCdbWrapper.nApplicationResumeDebuggerTime = None;
        oCdbWrapper.nApplicationResumeTime = None;
      finally:
        oCdbWrapper.oApplicationTimeLock.release();
      (
        sProcessIdHex,
        sCreateExitProcess, sCreateExitProcessIdHex,
        sExceptionDescription, sExceptionCode, sChance,
        sBreakpointId,
      ) = oEventMatch.groups();
      ### Handle the current process ###################################################################################
      oCurrentProcess = oCdbWrapper.foSetCurrentProcessAfterApplicationRan(
        uProcessId = long(sProcessIdHex, 16),
        sCreateOrExit = sCreateExitProcess,
      );
      ### Handle the exception/event ###############################################################################
      uExceptionCode = sExceptionCode and long(sExceptionCode, 16);
      uBreakpointId = sBreakpointId and long(sBreakpointId);
      # Creating a new process can trigger a create process event, a STATUS_BREAKPOINT and a STATUS_WX86_BREAKPOINT,
      # in that order. This sequence starts with either a create process event or a STATUS_BREAKPOINT. The first
      # exception informs us of the new process, but the rest are superfluous and should be ignored. To do that, we
      # have dict duIgnoreNextExceptionCode_by_uProcessId in which we store the exception code to ignore if it happens
      # next in this process.
      bIsIgnoredException = False;
      if oCurrentProcess.bNew:
        # If there are more processes to attach to, do so:
        if len(oCdbWrapper.auProcessIdsPendingAttach) > 0:
          asAttachToProcess = oCdbWrapper.fasSendCommandAndReadOutput( \
              ".attach 0n%d; $$ Attach to process" % oCdbWrapper.auProcessIdsPendingAttach[0]);
          if not oCdbWrapper.bCdbRunning: return;
        else:
          # Set up exception handling if this has not been done yet.
          if not oCdbWrapper.bExceptionHandlersHaveBeenSet:
            # Note to self: when rewriting the code, make sure not to set up exception handling before the debugger has
            # attached to all processes. But do so before resuming the threads. Otherwise one or more of the processes
            # can end up having only one thread that has a suspend count of 2 and no amount of resuming will cause the
            # process to run. The reason for this is unknown, but if things are done in the correct order, this problem
            # is avoided.
            oCdbWrapper.bExceptionHandlersHaveBeenSet = True;
            oCdbWrapper.fasSendCommandAndReadOutput("%s; $$ Setup exception handling" % sExceptionHandlingCommands);
            if not oCdbWrapper.bCdbRunning: return;
          # If the debugger attached to processes, mark that as done and resume threads in all processes.
          if bDebuggerNeedsToResumeAttachedProcesses:
            bDebuggerNeedsToResumeAttachedProcesses = False;
            for uProcessId in oCdbWrapper.doProcess_by_uId.keys():
              oCdbWrapper.fSelectProcess(uProcessId);
              if not oCdbWrapper.bCdbRunning: return;
              oCdbWrapper.fasSendCommandAndReadOutput("~*m; $$ Resume all threads");
              if not oCdbWrapper.bCdbRunning: return;
        if sCreateExitProcess == "Create":
          # Creating a new process can also throw a STATUS_BREAKPOINT; this exception should be ignored as we have
          # already handled the new process.
          duIgnoreNextExceptionCode_by_uProcessId[oCurrentProcess.uId] = STATUS_BREAKPOINT;
      elif oCurrentProcess.bTerminated:
        pass;
      elif oCurrentProcess.uId in duIgnoreNextExceptionCode_by_uProcessId and duIgnoreNextExceptionCode_by_uProcessId[oCurrentProcess.uId] == uExceptionCode:
        # This exception was expected and should be ignored.
        pass;
      else:
        if uExceptionCode == STATUS_BREAKPOINT:
          # A breakpoint can trigger a STATUS_BREAKPOINT exception followed by a STATUS_WX86_BREAKPOINT exception. The
          # later does not represent another event, so should be ignored.
          duIgnoreNextExceptionCode_by_uProcessId[oCurrentProcess.uId] = STATUS_WX86_BREAKPOINT;
        # Assume this exception is related to debugging and should not be reported to the application until we determine
        # otherwise in the code below:
        bPassLastExceptionToApplication = False;
        if uExceptionCode == DBG_CONTROL_BREAK:
          # The interrupt on timeout thread can send a CTRL+C to cdb, which causes a DBG_CONTROL_BREAK.
          # This allow this thread to check if timeout handlers should be fired and do so before resuming the
          # application.
          assert oCdbWrapper.uCdbBreakExceptionsPending > 0, \
            "cdb was interrupted unexpectedly";
          oCdbWrapper.uCdbBreakExceptionsPending -= 1;
        elif uBreakpointId is not None:
          # A breakpoint was hit; fire the callback
          fBreakpointCallback = oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
          fBreakpointCallback(uBreakpointId);
        elif uExceptionCode in [STATUS_BREAKPOINT, STATUS_WX86_BREAKPOINT] and \
            cCdbWrapper_fbDetectAndReportVerifierErrors(oCdbWrapper, asCdbOutput):
          # Application verifier reported something, which is always expected to have triggered this breakpoint.
          # The cCdbWrapper_fbDetectAndReportVerifierErrors will have created a report if one is needed, so there is
          # nothing left to do here.
          pass;
        else:
          # This exception is not related to debugging and should be analyzed to see if it's a bug. If it is not, it
          # should be passed and handled by the application:
          bPassLastExceptionToApplication = True;
          # If available, free previously allocated memory to allow analysis in low memory conditions.
          if bReserveRAMAllocated:
            # This command is not relevant to the bug, so it is hidden in the cdb IO to prevent OOM.
            oCdbWrapper.fasSendCommandAndReadOutput("ad RAM; $$ Release RAM");
            bReserveRAMAllocated = False;
          # Create a bug report, if the exception is fatal.
          oCdbWrapper.oBugReport = cBugReport.foCreateForException(oCdbWrapper, uExceptionCode, sExceptionDescription);
          if not oCdbWrapper.bCdbRunning: return;
      
      # See if a bug needs to be reported
      if oCdbWrapper.oBugReport is not None:
        oCdbWrapper.oBugReport.fPostProcess(oCdbWrapper);
        # Stop to report the bug.
        break;
      # Execute any pending timeout callbacks (this can happen when the interrupt on timeout thread has interrupted
      # the application or whenever the application is paused for another exception - the interrupt on timeout thread
      # is just there to make sure the application gets interrupted to do so when needed: otherwise the timeout may not
      # fire until an exception happens by chance)
      oCdbWrapper.oTimeoutsLock.acquire();
      try:
        axTimeoutsToFire = [];
        for xTimeout in oCdbWrapper.axTimeouts:
          (nTimeoutApplicationRunTime, fTimeoutCallback, axTimeoutCallbackArguments) = xTimeout;
          if nTimeoutApplicationRunTime <= oCdbWrapper.nApplicationRunTime: # This timeout should be fired.
            oCdbWrapper.axTimeouts.remove(xTimeout);
            axTimeoutsToFire.append((fTimeoutCallback, axTimeoutCallbackArguments));
#           print "@@@ firing timeout %.1f seconds late: %s" % (oCdbWrapper.nApplicationRunTime - nTimeoutApplicationRunTime, repr(fTimeoutCallback));
      finally:
        oCdbWrapper.oTimeoutsLock.release();
      for (fTimeoutCallback, axTimeoutCallbackArguments) in axTimeoutsToFire:
        fTimeoutCallback(*axTimeoutCallbackArguments);
    # Terminate cdb.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
    oCdbWrapper.fasSendCommandAndReadOutput("q");
  finally:
    oCdbWrapper.bCdbStdInOutThreadRunning = False;
    # Release the lock on cdb so the "interrupt on timeout" thread can notice cdb has terminated
    oCdbWrapper.oCdbLock.release();
  assert not oCdbWrapper.bCdbRunning, "Debugger did not terminate when requested";

