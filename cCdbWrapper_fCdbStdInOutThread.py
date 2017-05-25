import datetime, re, time;
from cBugReport import cBugReport;
from cCdbStoppedException import cCdbStoppedException;
from cDebuggerExtension import cDebuggerExtension;
from cProcess import cProcess;
from daxExceptionHandling import daxExceptionHandling;
from dxConfig import dxConfig;
from foDetectAndCreateBugReportForVERIFIER_STOP import foDetectAndCreateBugReportForVERIFIER_STOP;
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

# BugId will either start the process, or attach to it. 
def cCdbWrapper_fCdbStdInOutThread(oCdbWrapper):
  # cCdbWrapper initialization code already acquire a lock on cdb on behalf of this thread, so the "interrupt on
  # timeout" thread does not attempt to interrupt cdb while this thread is getting started.
  try:
    # There are situations where an exception should be handled by the debugger and not by the application, this
    # boolean is set to True to indicate this and is used to execute either "gh" or "gn" in cdb.
    bLetApplicationHandleCurrentException = False;
    # Sometime an event can trigger multiple exceptions but only the first one contains new information. For instance
    # when a new process is created, up to three exceptions can happen that are related this this event. In such cases
    # BugId may need to ignore all but the first such exception. to be able to ignore exceptions, a dict contains the
    # exception code of the exception to ignore for each process.
    dauIgnoreNextExceptionCodes_by_uProcessId = {};
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
    # Turn off prompt information as it is not useful most of the time, but can clutter output and slow down
    # debugging by loading and resolving symbols.
    oCdbWrapper.fasSendCommandAndReadOutput(".prompt_allow -dis -ea -reg -src -sym; $$ Display only the prompt");
    # Make sure the cdb prompt is on a new line after the application has been run:
    oCdbWrapper.fasSendCommandAndReadOutput('.pcmd -s ".echo;"; $$ Output a CRLF after running the application');
    # Load the debugger extension
    oCdbWrapper.oExtension = cDebuggerExtension.foLoad(oCdbWrapper);
    
    # Only fire fApplicationRunningCallback if the application was started for the first time or resumed after it was
    # paused to analyze an exception. 
    if len(oCdbWrapper.auProcessIdsPendingAttach) > 0:
      sStatus = "attaching to application";
    else:
      sStatus = "starting application";
    bAttachingToOrStartingApplication = True;
    bThreadsNeedToBeResumed = len(oCdbWrapper.auProcessIdsPendingAttach) > 0;
    # An bug report will be created when needed; it is returned at the end
    oBugReport = None;
    # Memory can be allocated to be freed later in case the system has run low on memory when an analysis needs to be
    # performed. This is done only if dxConfig["uReserveRAM"] > 0. The memory is allocated at the start of
    # debugging, freed right before an analysis is performed and reallocated if the exception was not fatal.
    uReserveRAMAllocated = 0;
    while (
      asIntialCdbOutput # We still need to process the initial cdb output
      or len(oCdbWrapper.auProcessIdsPendingAttach) > 0 # We still need to attach to more processes
      or (len(oCdbWrapper.doProcess_by_uId) > 1 or not oCdbWrapper.oCurrentProcess.bTerminated) # There are still processes running.
    ):
      if asIntialCdbOutput:
        # First parse the initial output
        asCdbOutput = asIntialCdbOutput;
        asIntialCdbOutput = None;
      else:
        ### Run timeout callbacks ######################################################################################
        # Execute any pending timeout callbacks (this can happen when the interrupt on timeout thread has interrupted
        # the application or whenever the application is paused for another exception - the interrupt on timeout thread
        # is just there to make sure the application gets interrupted to do so when needed: otherwise the timeout may not
        # fire until an exception happens by chance)
        axTimeoutsToFire = [];
        oCdbWrapper.oTimeoutsLock.acquire();
        try:
          for xTimeout in oCdbWrapper.axTimeouts:
            (nTimeoutApplicationRunTime, fTimeoutCallback, axTimeoutCallbackArguments) = xTimeout;
            if nTimeoutApplicationRunTime <= oCdbWrapper.nApplicationRunTime: # This timeout should be fired.
              oCdbWrapper.axTimeouts.remove(xTimeout);
              axTimeoutsToFire.append((fTimeoutCallback, axTimeoutCallbackArguments));
#             print "@@@ firing timeout %.1f seconds late: %s" % (oCdbWrapper.nApplicationRunTime - nTimeoutApplicationRunTime, repr(fTimeoutCallback));
        finally:
          oCdbWrapper.oTimeoutsLock.release();
        for (fTimeoutCallback, axTimeoutCallbackArguments) in axTimeoutsToFire:
          fTimeoutCallback(*axTimeoutCallbackArguments);
          # The callback may have reported a bug, in which case we're done.
          if oCdbWrapper.oBugReport: break;
        if oCdbWrapper.oBugReport: break;
        ### Attaching to or starting application #######################################################################
        if bAttachingToOrStartingApplication:
          if len(oCdbWrapper.auProcessIdsPendingAttach) > 0:
            # There are more processes to attach to:
            asAttachToProcess = oCdbWrapper.fasSendCommandAndReadOutput( \
                ".attach 0x%X; $$ Attaching to another process" % oCdbWrapper.auProcessIdsPendingAttach[0]);
          else:
            # We attached to or started the application, set up exception handling and resume threads if needed.
            # Note to self: when rewriting the code, make sure not to set up exception handling before the debugger has
            # attached to all processes. But do so before resuming the threads. Otherwise one or more of the processes
            # can end up having only one thread that has a suspend count of 2 and no amount of resuming will cause the
            # process to run. The reason for this is unknown, but if things are done in the correct order, this problem
            # is avoided.
            oCdbWrapper.fasSendCommandAndReadOutput("%s; $$ Setup exception handling" % sExceptionHandlingCommands);
            if bThreadsNeedToBeResumed:
              # If the debugger attached to processes, resume threads in all processes.
              for uProcessId in oCdbWrapper.doProcess_by_uId.keys():
                oCdbWrapper.fSelectProcess(uProcessId);
                oCdbWrapper.fasSendCommandAndReadOutput("~*m; $$ Resume all threads");
              oCdbWrapper.fasSendCommandAndReadOutput(
                '.printf "Attaching to the application is complete and all threads have been resumed.\\r\\n";',
                bShowCommandInHTMLReport = False,
              );
            else:
              oCdbWrapper.fasSendCommandAndReadOutput(
                '.printf "Starting the application is complete.\\r\\n";',
                bShowCommandInHTMLReport = False,
              );
            oCdbWrapper.fApplicationRunningCallback();
            bAttachingToOrStartingApplication = False;
        else:
          oCdbWrapper.fApplicationResumedCallback();
        ### Check if page heap is enabled in all processes if requested ################################################
        if dxConfig["bEnsurePageHeap"]:
          for uProcessId, oProcess in oCdbWrapper.doProcess_by_uId.items():
            if not oProcess.bTerminated:
              oProcess.fEnsurePageHeapIsEnabled();
            elif uProcessId in dauIgnoreNextExceptionCodes_by_uProcessId:
              del dauIgnoreNextExceptionCodes_by_uProcessId[uProcessId];
        ### Discard cached information about processes #################################################################
        for oProcess in oCdbWrapper.doProcess_by_uId.values():
          # All processes will no longer be new.
          oProcess.bNew = False;
          # All processes that were terminated should be removed from the list of known processes:
          if oProcess.bTerminated:
            del oCdbWrapper.doProcess_by_uId[oProcess.uId];
          else:
            # Any cached information about modules loaded in the process should be discarded
            oProcess.fClearCache();
        # There will no longer be a current process.
        oCdbWrapper.oCurrentProcess = None;
        ### Reserve RAM if requested ###################################################################################
        # If requested, reserve some memory in cdb that can be released later to make analysis under low memory conditions
        # more likely to succeed.
        if dxConfig["uReserveRAM"] and uReserveRAMAllocated == 0:
          uBitMask = 2 ** 31;
          while uBitMask >= 1:
            sBit = dxConfig["uReserveRAM"] & uBitMask and "A" or "";
            if uReserveRAMAllocated:
              uReserveRAMAllocated *= 2;
              if dxConfig["uReserveRAM"] & uBitMask:
                sAdditionalByte = "A";
                uReserveRAMAllocated += 1;
              else:
                sAdditionalByte = "";
              oCdbWrapper.fasSendCommandAndReadOutput(
                  'aS /c ${/v:RAM} ".printf \\"${RAM}${RAM}%s\\";"; $$ Allocate %d bytes of RAM' %
                  (sAdditionalByte, uReserveRAMAllocated));
            elif dxConfig["uReserveRAM"] & uBitMask:
              oCdbWrapper.fasSendCommandAndReadOutput('aS ${/v:RAM} "A"; $$ Allocate 1 byte of RAM');
              uReserveRAMAllocated = 1;
            uBitMask /= 2;
        ### Keep track of time #########################################################################################
        # Mark the time when the application was resumed.
        asCdbTimeOutput = oCdbWrapper.fasSendCommandAndReadOutput(".time; $$ Get debugger time");
        oTimeMatch = len(asCdbTimeOutput) > 0 and re.match(r"^Debug session time: (.*?)\s*$", asCdbTimeOutput[0]);
        assert oTimeMatch, "Failed to get debugger time!\r\n%s" % "\r\n".join(asCdbTimeOutput);
        del asCdbTimeOutput;
        oCdbWrapper.oApplicationTimeLock.acquire();
        try:
          oCdbWrapper.nApplicationResumeDebuggerTime = fnGetDebuggerTime(oTimeMatch.group(1));
          oCdbWrapper.nApplicationResumeTime = time.clock();
        finally:
          oCdbWrapper.oApplicationTimeLock.release();
        ### Resume application #########################################################################################
        # Release the lock on cdb so the "interrupt on timeout" thread can attempt to interrupt cdb while the
        # application is running.
        if len(oCdbWrapper.auProcessIdsPendingAttach) == 0:
          oCdbWrapper.oCdbLock.release();
        sRunApplicationCommand = bLetApplicationHandleCurrentException and "gn" or "gh";
        bLetApplicationHandleCurrentException = False; # Assume we'll be handling the next exception ourselves.
        sRunApplicationComment = bAttachingToOrStartingApplication and (
          "Attaching to process %d/0x%X" % (oCdbWrapper.auProcessIdsPendingAttach[0], oCdbWrapper.auProcessIdsPendingAttach[0])
        ) or (
          "Running application"
        );
        try:
          asCdbOutput = oCdbWrapper.fasSendCommandAndReadOutput(
            "%s; $$ %s" % (sRunApplicationCommand, sRunApplicationComment),
            bShowCommandInHTMLReport = False,
            bOutputIsInformative = True,
            bOutputCanContainApplicationOutput = True,
            bUseMarkers = False, # This does not work with g commands: the end marker will never be shown.
          );
        finally:
          # Get a lock on cdb so the "interrupt on timeout" thread does not attempt to interrupt cdb while we execute
          # commands.
          if len(oCdbWrapper.auProcessIdsPendingAttach) == 0:
            oCdbWrapper.oCdbLock.acquire();
      ### An exception was detected ####################################################################################
      # Find out what event caused the debugger break
      # I have been experiencing a bug where the next command I want to execute (".lastevent") returns nothing. This
      # appears to be caused by an error while executing the command (without an error message) as subsequent commands
      # are not getting executed. As a result, the .printf that outputs the "end marker" is never executed and
      # `fasReadOutput` detects this as an error in the command and throws an exception. This mostly just affects the
      # next command executed at this point, but I've also seen it affect the second, so I'm going to try and work
      # around it by providing a `bRetryOnTruncatedOutput` argument that informs `fasSendCommandAndReadOutput` to
      # detect this truncated output and try the command again for any command that we can safely execute twice.
      asLastEventOutput = oCdbWrapper.fasSendCommandAndReadOutput(".lastevent; $$ Get information about last event",
        bOutputIsInformative = True,
        bRetryOnTruncatedOutput = True,
      );
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
      uProcessId = long(sProcessIdHex, 16);
      assert not sCreateExitProcessIdHex or sProcessIdHex == sCreateExitProcessIdHex, \
          "This is highly unexpected";
      uExceptionCode = sExceptionCode and long(sExceptionCode, 16);
      bApplicationCannotHandleException = sChance == "second";
      uBreakpointId = sBreakpointId and long(sBreakpointId);
      # If the application was not suspended on purpose to attach to another process, report it:
      if not bAttachingToOrStartingApplication:
        if uBreakpointId is not None:
          sReason = "breakpoint hit";
        elif uExceptionCode is not None:
          sReason = "%s chance exception 0x%08X" % (sChance, uExceptionCode);
        elif sCreateExitProcess == "Create":
          sReason = "new process";
        else:
          sReason = "process terminated";
        oCdbWrapper.fApplicationSuspendedCallback(sReason);
      ### See if it was a debugger break-in for a new process that failed to load properly #############################
      if uExceptionCode == STATUS_WAKE_SYSTEM_DEBUGGER:
        # This exception does not always get reported for the new process; see if there are any processes known to cdb
        # that we do not yet know about:
        asListProcesses = oCdbWrapper.fasSendCommandAndReadOutput("|;", bRetryOnTruncatedOutput = True);
        auNewProcessIds = [];
        for sListProcess in asListProcesses:
          oProcessIdMatch = re.match("[#\.\s]+\d+\s+id:\s+([0-9a-f]+)\s+.*", sListProcess, re.I);
          assert oProcessIdMatch, \
              "Unrecognized process list output: %s\r\n%s" % (repr(sListProcess), "\r\n".join(asListProcesses));
          uPotentiallNewProcessId = long(oProcessIdMatch.group(1), 16);
          if uPotentiallNewProcessId not in oCdbWrapper.doProcess_by_uId:
            auNewProcessIds.append(uPotentiallNewProcessId);
        #  We're expecting there to be at most 1:
        assert len(auNewProcessIds) < 2, \
            "Found %d new processes: %s" % (len(auNewProcessIds), ", ".join([str(u) for u in auNewProcessIds]));
        if len(auNewProcessIds) == 1:
          # This process is new, handle it.
          uProcessId = auNewProcessIds[0];
      ### Determine the current process ################################################################################
      if uProcessId not in oCdbWrapper.doProcess_by_uId:
        # Create a new process object and make it the current process.
        oCdbWrapper.doProcess_by_uId[uProcessId] = oCdbWrapper.oCurrentProcess = cProcess(oCdbWrapper, uProcessId);
        assert oCdbWrapper.oCurrentProcess.uId == uProcessId, \
            "Expected the current process to be %d/0x%X but got %d/0x%X" % \
            (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.uId, oCdbWrapper.oCurrentProcess.uId);
        # Make it a main process to if we're still attaching to or starting the application
        if bAttachingToOrStartingApplication:
          oCdbWrapper.aoMainProcesses.append(oCdbWrapper.oCurrentProcess);
          # If we are attaching to processes, the current process should be the last one we tried to attach to:
          if oCdbWrapper.auProcessIdsPendingAttach:
            uPendingAttachProcessId = oCdbWrapper.auProcessIdsPendingAttach.pop(0);
            assert uPendingAttachProcessId == uProcessId, \
                "Expected to attach to process %d, got %d" % (uPendingAttachProcessId, uProcessId);
            oCdbWrapper.fasSendCommandAndReadOutput(
              '.printf "Attached to process %d/0x%X (%s).\\r\\n";' % (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName),
              bShowCommandInHTMLReport = False,
            );
          else:
            oCdbWrapper.fasSendCommandAndReadOutput(
              '.printf "Started process %d/0x%X (%s).\\r\\n";' % (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName),
              bShowCommandInHTMLReport = False,
            );
        # Make sure child processes of the new process are debugged as well.
        oCdbWrapper.fasSendCommandAndReadOutput(".childdbg 1; $$ Debug child processes", bRetryOnTruncatedOutput = True);
        if sCreateExitProcess == "Create":
          # If the application creates a new process, a STATUS_BREAKPOINT exception may follow that signals the
          # same event; this exception should be ignored as we have already handled the new process.
          # This is potentially unreliable: if this exception is not thrown, but the process does trigger a
          # breakpoint for some other reason, it will be ignored. However, I have never seen that happen.
          dauIgnoreNextExceptionCodes_by_uProcessId[uProcessId] = [STATUS_BREAKPOINT];
          if oCdbWrapper.sCdbISA == "x64" and oCdbWrapper.oCurrentProcess.sISA == "x86":
            dauIgnoreNextExceptionCodes_by_uProcessId[uProcessId].append(STATUS_WX86_BREAKPOINT);
        # This event was explicitly to notify us of the new process; no more processing is needed.
        continue;
      else:
        oCdbWrapper.oCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
      ### See if this was an ignored exception #########################################################################
      auIgnoreNextExceptionCodes = dauIgnoreNextExceptionCodes_by_uProcessId.get(uProcessId);
      if auIgnoreNextExceptionCodes:
        assert uExceptionCode == auIgnoreNextExceptionCodes[0], \
          "Expected to see exception 0x%X in %s process, but got 0x%X!?" % \
            (auIgnoreNextExceptionCodes[0], oCdbWrapper.oCurrentProcess.sBinaryName, uExceptionCode);        
        # Ignore this exception
        oCdbWrapper.fasSendCommandAndReadOutput(
          '.printf "This exception is assumed to be related to a recent process creation and therefore ignored.\\r\\n";',
          bShowCommandInHTMLReport = False,
        );
        auIgnoreNextExceptionCodes.pop(0);
        # If there are no more exceptions to be ignored for this process, stop ignoring exceptions.
        if len(auIgnoreNextExceptionCodes) == 0:
          del dauIgnoreNextExceptionCodes_by_uProcessId[uProcessId];
        continue;
      ### Handle process termination ###################################################################################
      if sCreateExitProcess == "Exit":
        assert not bAttachingToOrStartingApplication, \
            "No processes are expected to terminated while attaching to or starting the application!";
        # A process was terminated. This may be the first time we hear of the process, i.e. the code above may have only
        # just added the process. I do not know why cdb did not throw an event when it was created: maybe it terminated
        # while being created due to some error? Anyway, having added the process in the above code, we'll now mark it as
        # terminated:
        oCdbWrapper.oCurrentProcess.bTerminated = True;
        if oCdbWrapper.oCurrentProcess in oCdbWrapper.aoMainProcesses:
          oCdbWrapper.fMainProcessTerminatedCallback(uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName);
          oCdbWrapper.fasSendCommandAndReadOutput(
            '.printf "Terminated main process %d/0x%X (%s).\\r\\n";' % (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName),
            bShowCommandInHTMLReport = False,
          );
        else:
          oCdbWrapper.fasSendCommandAndReadOutput(
            '.printf "Terminated sub-process %d/0x%X (%s).\\r\\n";' % (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName),
            bShowCommandInHTMLReport = False,
          );
        # This event was explicitly to notify us of the terminated process; no more processing is needed.
        continue;
      assert not bAttachingToOrStartingApplication, \
          "No exceptions are expected while attaching to or starting the application!";
      # If available, free previously allocated memory to allow analysis in low memory conditions.
      if uReserveRAMAllocated:
        # This command is not relevant to the bug, so it is hidden in the cdb IO to prevent OOM.
        oCdbWrapper.fasSendCommandAndReadOutput("ad ${/v:RAM}; $$ Release RAM");
        uReserveRAMAllocated = 0;
      ### Handle timeout interrupt #####################################################################################
      if uExceptionCode == DBG_CONTROL_BREAK:
        # The interrupt on timeout thread can send a CTRL+C to cdb, which causes a DBG_CONTROL_BREAK.
        # This allow this thread to check if timeout handlers should be fired and do so before resuming the
        # application.
        assert oCdbWrapper.uCdbBreakExceptionsPending > 0, \
          "cdb was interrupted unexpectedly";
        oCdbWrapper.fasSendCommandAndReadOutput(
          '.printf "The application was interrupted to handle a timeout.\\r\\n";',
          bShowCommandInHTMLReport = False,
        );
        oCdbWrapper.uCdbBreakExceptionsPending -= 1;
        continue;
      ### Handle hit breakpoint ########################################################################################
      if uBreakpointId is not None:
        # A breakpoint was hit; fire the callback
        oCdbWrapper.fasSendCommandAndReadOutput(
          '.printf "The application hit a breakpoint.\\r\\n";',
          bShowCommandInHTMLReport = False,
        );
        fBreakpointCallback = oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
        fBreakpointCallback(uBreakpointId);
        continue;
      ### Analyze potential bugs #######################################################################################
      oCdbWrapper.fasSendCommandAndReadOutput(
        '.printf "Analyzing unexpected exception.\\r\\n";',
        bShowCommandInHTMLReport = False,
      );
      ### Handle VERIFIER STOP #########################################################################################
      oBugReport = foDetectAndCreateBugReportForVERIFIER_STOP(oCdbWrapper, uExceptionCode, asCdbOutput);
      if oBugReport and oBugReport.sBugTypeId is not None:
        # VERIFIER STOP detected.
        oCdbWrapper.oBugReport = oBugReport;
        break;
      ### Handle bugs ##################################################################################################
      # If this exception is considered Create a bug report for the exception and stop debugging if it is indeed considerd a bug.
      oBugReport = cBugReport.foCreateForException(oCdbWrapper, uExceptionCode, sExceptionDescription, bApplicationCannotHandleException);
      if oBugReport and oBugReport.sBugTypeId is not None:
        oCdbWrapper.oBugReport = oBugReport;
        break;
      # This exception was not expected, but it's not considered a bug: let the application handle it.
      bLetApplicationHandleException = True;
    
    ### Done ###
    if oCdbWrapper.oBugReport is not None:
      oCdbWrapper.oBugReport.fPostProcess(oCdbWrapper);
    # Terminate cdb.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
    oCdbWrapper.fasSendCommandAndReadOutput("q", bIgnoreOutput = True, bUseMarkers = False); # This is not going to end up in the report.
  except cCdbStoppedException as oCdbStoppedException:
    pass;
  finally:
    oCdbWrapper.bCdbStdInOutThreadRunning = False;
    # Release the lock on cdb so the "interrupt on timeout" thread can notice cdb has terminated
    oCdbWrapper.oCdbLock.release();
  assert not oCdbWrapper.bCdbRunning, "Debugger did not terminate when requested";

