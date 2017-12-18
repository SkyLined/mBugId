import datetime, re, time;
from cBugReport import cBugReport;
from cCdbStoppedException import cCdbStoppedException;
from cProcess import cProcess;
from dxConfig import dxConfig;
from foDetectAndCreateBugReportForVERIFIER_STOP import foDetectAndCreateBugReportForVERIFIER_STOP;
from foDetectAndCreateBugReportForASan import foDetectAndCreateBugReportForASan;
from fsExceptionHandlingCdbCommands import fsExceptionHandlingCdbCommands;
from mWindowsAPI import cJobObject, fbTerminateThreadForId, cVirtualAllocation, \
    cConsoleProcess, fsGetProcessISAForId, fbTerminateProcessForId;
from mWindowsAPI.mDefines import *;

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
  # Create a job object to limit memory use if requested:
  if oCdbWrapper.uProcessMaxMemoryUse is not None or oCdbWrapper.uTotalMaxMemoryUse is not None:
    oJobObject = cJobObject();
    if oCdbWrapper.uProcessMaxMemoryUse is not None:
      oJobObject.fSetMaxProcessMemoryUse(oCdbWrapper.uProcessMaxMemoryUse);
    if oCdbWrapper.uTotalMaxMemoryUse is not None:
      oJobObject.fSetMaxTotalMemoryUse(oCdbWrapper.uTotalMaxMemoryUse);
  else:
    oJobObject = None;
  # If we cannot apply memory limits, we'll fire an event. This should be done only once.
  bFailedToApplyApplicationMemoryLimitsEventFired = True;
  # We may want to reserve some memory, which we'll track using this variable
  oReservedMemoryVirtualAllocation = None;
  # There are situations where an exception should be handled by the debugger and not by the application, this
  # boolean is set to True to indicate this and is used to execute either "gh" or "gn" in cdb.
  bHideLastExceptionFromApplication = False;
  # Sometime an event can trigger multiple exceptions but only the first one contains new information. For instance
  # when a new process is created, up to three exceptions can happen that are related this this event. In such cases
  # BugId may need to ignore all but the first such exception. to be able to ignore exceptions, a dict contains the
  # exception code of the exception to ignore for each process.
  dauIgnoreNextExceptionCodes_by_uProcessId = {};
  # Create a list of commands to set up event handling.
  sExceptionHandlingCommands = fsExceptionHandlingCdbCommands();
  
  # Read the initial cdb output related to starting/attaching to the first process.
  asIntialCdbOutput = oCdbWrapper.fasReadOutput();
  # Turn off prompt information as it is not useful most of the time, but can clutter output and slow down
  # debugging by loading and resolving symbols.
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".prompt_allow -dis -ea -reg -src -sym;",
    sComment = "Display only the prompt",
  );
  # Make sure the cdb prompt is on a new line after the application has been run:
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = '.pcmd -s ".echo;";',
    sComment = "Output a CRLF after running the application",
  );
  if len(oCdbWrapper.auProcessIdsPendingAttach) > 0:
    sStatus = "attaching to application";
  else:
    sStatus = "starting application";
  auProcessIdsThatNeedToBeResumed = [];
  bLastExceptionWasIgnored = False;
  # We start a utility process in which we can trigger breakpoints to distinguish them from breakpoints in the
  # target application.
  # The application needs to be started, but only once, so we set a flag to remind us to do so and unset it when it's done.
  bApplicationNeedsToBeStarted = oCdbWrapper.oUWPApplication or oCdbWrapper.sApplicationBinaryPath;
  bCdbHasAttachedToApplication = False;
  # When a new process is created, stdout/stderr reading threads are created. These will not stop reading when the
  # process terminates, so we need to close these handles when it does. In order to do that we track them here:
  # An bug report will be created when needed; it is returned at the end
  oBugReport = None;
  while ( # run this loop while...
    # ... we still need to start the application ...
    bApplicationNeedsToBeStarted
    # ... or we still need to attach to processes ...
    or len(oCdbWrapper.auProcessIdsPendingAttach) > 0 
    # ... or there is at least one process running for the application ...
    or len([oProcess for oProcess in oCdbWrapper.doProcess_by_uId.values() if not oProcess.bTerminated]) >= 1
  ) and (
    # ... and no fatal bugs have been detected.
    not oCdbWrapper.bFatalBugDetected
  ):
    if asIntialCdbOutput:
      # First parse the initial output
      asUnprocessedCdbOutput = asIntialCdbOutput;
      asIntialCdbOutput = None;
    else:
      ### Run timeout callbacks ######################################################################################
      # Execute any pending timeout callbacks (this can happen when the interrupt on timeout thread has interrupted
      # the application or whenever the application is paused for another exception - the interrupt on timeout thread
      # is just there to make sure the application gets interrupted to do so when needed: otherwise the timeout may not
      # fire until an exception happens by chance).
      while 1:
        # Timeouts can create new timeouts, which may need to fire immediately, so this is run in a loop until no more
        # timeouts need to be fired.
        aoTimeoutsToFire = [];
        oCdbWrapper.oTimeoutAndInterruptLock.acquire();
        try:
          for oTimeout in oCdbWrapper.aoTimeouts[:]:
            if oTimeout.fbShouldFire(oCdbWrapper.nApplicationRunTime):
              oCdbWrapper.aoTimeouts.remove(oTimeout);
              aoTimeoutsToFire.append(oTimeout);
        finally:
          oCdbWrapper.oTimeoutAndInterruptLock.release();
        if not aoTimeoutsToFire:
          break;
        for oTimeoutToFire in aoTimeoutsToFire:
          oTimeoutToFire.fFire();
      ### Attaching to or starting application #######################################################################
      if bLastExceptionWasIgnored:
        # We really shouldn't do anything at the moment because the last exception was a bit odd; e.g. one of the
        # various events that are triggered by a new process.
        bLastExceptionWasIgnored = False;
      elif len(oCdbWrapper.auProcessIdsPendingAttach) > 0:
        # There are more processes to attach to:
        uProcessId = oCdbWrapper.auProcessIdsPendingAttach[0];
        if not oCdbWrapper.fbAttachToProcessForId(uProcessId):
          sMessage = "Unable to attach to process %d/0x%X" % (uProcessId, uProcessId);
          assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
              sMessage;
          oCdbWrapper.fTerminate();
          return;
      elif bApplicationNeedsToBeStarted:
        if oCdbWrapper.oUWPApplication:
          # Kill it so we are sure to run a fresh copy.
          asTerminateUWPApplicationOutput = oCdbWrapper.fasExecuteCdbCommand(
            sCommand = ".terminatepackageapp %s;" % oCdbWrapper.oUWPApplication.sPackageFullName,
            sComment = "Terminate UWP application %s" % oCdbWrapper.oUWPApplication.sPackageName,
          );
          if asTerminateUWPApplicationOutput:
            assert asTerminateUWPApplicationOutput == ['The "terminatePackageApp" action will be completed on next execution.'], \
                "Unexpected .terminatepackageapp output:\r\n%s" % "\r\n".join(asTerminateUWPApplicationOutput);
          if len(oCdbWrapper.asApplicationArguments) == 0:
            # Note that the space between the application id and the command-terminating semi-colon MUST be there to
            # make sure the semi-colon is not interpreted as part of the application id!
            sStartUWPApplicationCommand = ".createpackageapp %s %s ;" % \
                (oCdbWrapper.oUWPApplication.sPackageFullName, oCdbWrapper.oUWPApplication.sApplicationId);
          else:
            # This check should be superfluous, but it doesn't hurt to make sure.
            assert len(oCdbWrapper.asApplicationArguments) == 1, \
                "Expected exactly one argument";
            # Note that the space between the argument and the command-terminating semi-colon MUST be there to make
            # sure the semi-colon is not passed to the UWP app as part of the argument!
            sStartUWPApplicationCommand = ".createpackageapp %s %s %s ;" % \
                (oCdbWrapper.oUWPApplication.sPackageFullName, oCdbWrapper.oUWPApplication.sApplicationId, oCdbWrapper.asApplicationArguments[0]);
          asStartUWPApplicationOutput = oCdbWrapper.fasExecuteCdbCommand(
            sCommand = sStartUWPApplicationCommand,
            sComment = "Start UWP application %s" % oCdbWrapper.oUWPApplication.sPackageName,
          );
          assert asStartUWPApplicationOutput == ["Attach will occur on next execution"], \
              "Unexpected .createpackageapp output: %s" % repr(asStartUWPApplicationOutput);
        else:
          oConsoleProcess = cConsoleProcess.foCreateForBinaryPathAndArguments(
            sBinaryPath = oCdbWrapper.sApplicationBinaryPath,
            asArguments = oCdbWrapper.asApplicationArguments,
            bRedirectStdIn = False,
            bSuspended = True,
          );
          if oConsoleProcess is None:
            sMessage = "Unable to start a new process for binary \"%s\"." % oCdbWrapper.sApplicationBinaryPath;
            assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
                sMessage;
            oCdbWrapper.fTerminate();
            return;
          oCdbWrapper.doConsoleProcess_by_uId[oConsoleProcess.uId] = oConsoleProcess;
          # a 32-bit debugger cannot debug 64-bit processes. Report this.
          if oCdbWrapper.sCdbISA == "x86":
            if fsGetProcessISAForId(oConsoleProcess.uId) == "x64":
              assert fbTerminateProcessForId(oConsoleProcess.uId), \
                  "failed to terminate recently started process %d/0x%X" % \
                  (oConsoleProcess.uId, oConsoleProcess.uId);
              sMessage = "Unable to debug a 64-bit process using 32-bit cdb.";
              assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
                  sMessage;
              oCdbWrapper.fTerminate();
              return;
          oCdbWrapper.fLogMessageInReport(
            "LogProcess",
            "Process %d was started using binary %s and arguments %s." % \
                (oConsoleProcess.uId, repr(oCdbWrapper.sApplicationBinaryPath), repr(oCdbWrapper.asApplicationArguments)),
          );
          # Create helper threads that read the application's output to stdout and stderr. No references to these
          # threads are saved, as they are not needed: these threads only exist to read stdout/stderr output from the
          # application and save it in the report. They will self-terminate when oConsoleProcess.fClose() is called
          # after the process terminates, or this cdb stdio thread dies.
          sBinaryName = oConsoleProcess.oInformation.sBinaryName;
          sCommandLine = oConsoleProcess.oInformation.sCommandLine;
          oCdbWrapper.foHelperThread(
              oCdbWrapper.fApplicationStdOutOrErrThread,
              oConsoleProcess.uId, sBinaryName, sCommandLine, oConsoleProcess.oStdOutPipe, "StdOut",
          ).start();
          oCdbWrapper.foHelperThread(
              oCdbWrapper.fApplicationStdOutOrErrThread,
              oConsoleProcess.uId, sBinaryName, sCommandLine, oConsoleProcess.oStdErrPipe, "StdErr",
          ).start();
          # Tell cdb to attach to the process.
          if not oCdbWrapper.fbAttachToProcessForId(oConsoleProcess.uId):
            sMessage = "Unable to attach to new process %d/0x%X" % (oConsoleProcess.uId, oConsoleProcess.uId);
            assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
                sMessage;
            oCdbWrapper.fTerminate();
            return;
          auProcessIdsThatNeedToBeResumed.append(oConsoleProcess.uId);
        bApplicationNeedsToBeStarted = False; # We completed this task.
      else:
        # We are not attaching to or starting the application, so the application should now be run. If this is the
        # first time, call the `fApplicationRunningCallback`:
        if not bCdbHasAttachedToApplication:
          bCdbHasAttachedToApplication = True;
          oCdbWrapper.fbFireEvent("Application running");
        # if threads in any process need to be resumed, do so:
        while auProcessIdsThatNeedToBeResumed:
          uProcessId = auProcessIdsThatNeedToBeResumed.pop();
          oProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
          oProcess.fasExecuteCdbCommand(
            sCommand = "~*m;",
            sComment = "Resume all threads",
          );
          oCdbWrapper.fLogMessageInReport(
            "LogProcess",
            "All threads in process %d have been resumed." % uProcessId,
          );
      ### Check if page heap is enabled in all processes and discard cached info #####################################
      for uProcessId, oProcess in oCdbWrapper.doProcess_by_uId.items():
        if not oProcess.bTerminated:
          if dxConfig["bEnsurePageHeap"]:
            oProcess.fEnsurePageHeapIsEnabled();
        elif uProcessId in dauIgnoreNextExceptionCodes_by_uProcessId:
          del dauIgnoreNextExceptionCodes_by_uProcessId[uProcessId];
      ### Call application resumed callback before throwing away cached information ##################################
      oCdbWrapper.fbFireEvent("Application resumed");
      ### Discard cached information about processes #################################################################
      for (uProcessId, oProcess) in oCdbWrapper.doProcess_by_uId.items():
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
      ### Allocate reserve memory ####################################################################################
      # Reserve some memory for exception analysis in case the target application causes a system-wide low-memory
      # situation.
      if dxConfig["uReservedMemory"]:
        if oReservedMemoryVirtualAllocation is None:
          try:
            oReservedMemoryVirtualAllocation = cVirtualAllocation.foCreateInProcessForId(
              uProcessId = oCdbWrapper.oCdbProcess.pid,
              uSize = dxConfig["uReservedMemory"],
            );
          except MemoryError:
            pass; # If we cannot allocate memory, we'll just continue anyway.
      ### Keep track of time #########################################################################################
      # Mark the time when the application was resumed.
      asCdbTimeOutput = oCdbWrapper.fasExecuteCdbCommand(
        sCommand = ".time;",
        sComment = "Get debugger time",
        bRetryOnTruncatedOutput = True,
      );
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
      if oCdbWrapper.auProcessIdsPendingAttach:
        sRunApplicationComment = "Attaching to process %d/0x%X" % (oCdbWrapper.auProcessIdsPendingAttach[0], oCdbWrapper.auProcessIdsPendingAttach[0]);
      elif oCdbWrapper.oUWPApplication:
        sRunApplicationComment = "Starting UWP application %s" % oCdbWrapper.oUWPApplication.sPackageName;
      else:
        sRunApplicationComment = "Running application";
      asUnprocessedCdbOutput += oCdbWrapper.fasExecuteCdbCommand(
        sCommand = "g%s;" % (bHideLastExceptionFromApplication and "h" or "n"),
        sComment = sRunApplicationComment,
        bOutputIsInformative = True,
        bApplicationWillBeRun = True, # This command will cause the application to run.
        bUseMarkers = False, # This does not work with g commands: the end marker will never be shown.
      );
      # The application should handle the next exception unless we explicitly want it to be hidden
      bHideLastExceptionFromApplication = True;
    ### The debugger suspended the application #######################################################################
    # Send a nop command to cdb in case the application being debugged is reading stdin as well: in that case it may
    # eat the first char we try to send to cdb, which would otherwise cause a problem when cdb see only the part of
    # the command after the first char.
    oCdbWrapper.fasExecuteCdbCommand(
      sCommand = " ",
      sComment = None,
      bIgnoreOutput = True,
      bUseMarkers = False,
    );
    ### Handle the event #############################################################################################
    # I have been experiencing a bug where the next command I want to execute (".lastevent") returns nothing. This
    # appears to be caused by an error while executing the command (without an error message) as subsequent commands
    # are not getting executed. As a result, the .printf that outputs the "end marker" is never executed and
    # `fasReadOutput` detects this as an error in the command and throws an exception. This mostly just affects the
    # next command executed at this point, but I've also seen it affect the second, so I'm going to try and work
    # around it by providing a `bRetryOnTruncatedOutput` argument that informs `fasExecuteCdbCommand` to
    # detect this truncated output and try the command again for any command that we can safely execute twice.
    asLastEventOutput = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = ".lastevent;",
      sComment = "Get information about last event",
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
        r"Last event: ([0-9a-f]+)\.([0-9a-f]+): ",
        r"(?:",
          r"(Create|Exit) process [0-9a-f]+\:([0-9a-f]+)(?:, code [0-9a-f]+)?",
        r"|",
          r"(Ignored unload module at [0-9`a-f]+)", # Don't ask why cdb decides to report this, but I've seen it happen after a VERIFIER STOP.
                                                   # and yes; it should just report a breakpoint instead... sigh.
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
        oCdbWrapper.nConfirmedApplicationRunTime += fnGetDebuggerTime(oEventTimeMatch.group(1)) - oCdbWrapper.nApplicationResumeDebuggerTime;
      # Mark the application as suspended by setting nApplicationResumeDebuggerTime to None.
      oCdbWrapper.nApplicationResumeDebuggerTime = None;
      oCdbWrapper.nApplicationResumeTime = None;
    finally:
      oCdbWrapper.oApplicationTimeLock.release();
    (
      sProcessIdHex, sThreadIdHex,
      sCreateExitProcess, sCreateExitProcessIdHex,
      sIgnoredUnloadModule,
      sExceptionDescription, sExceptionCode, sChance,
      sBreakpointId,
    ) = oEventMatch.groups();
    if sIgnoredUnloadModule:
      # This exception makes no sense; ignore it.
      bLastExceptionWasIgnored = True;
      continue;
    uProcessId = long(sProcessIdHex, 16);
    uThreadId = long(sThreadIdHex, 16);
    assert not sCreateExitProcessIdHex or sProcessIdHex == sCreateExitProcessIdHex, \
        "This is highly unexpected";
    uExceptionCode = sExceptionCode and long(sExceptionCode, 16);
    bApplicationCannotHandleException = sChance == "second";
    uBreakpointId = sBreakpointId and long(sBreakpointId);
    ### Handle exceptions in the utility process #####################################################################
    if oCdbWrapper.uUtilityProcessId is None:
      assert uExceptionCode == STATUS_BREAKPOINT, \
          "An unexpected exception 0x%08X happened in process %d/0x%X, thread %d/0x%X before the debugger has attached to the utility process!" % \
          (uExceptionCode, uProcessId, uProcessId, uThreadId, uThreadId);
      # The first exception is the breakpoint triggered after creating the processes.
      # Set up exception handling and record the utility process' id.
      oCdbWrapper.uUtilityProcessId = uProcessId;
      oCdbWrapper.fasExecuteCdbCommand(
        sCommand = sExceptionHandlingCommands,
        sComment = "Setup exception handling",
      );
      oCdbWrapper.fLogMessageInReport(
        "LogProcess",
        "Started utility process %d/0x%X." % (uProcessId, uProcessId),
      );
      continue;
    elif oCdbWrapper.uUtilityProcessId == uProcessId:
      # TODO: no exceptions other than the AVs caused deliberately by us are expected. I would like to have an assert
      # here, but I found that this happened frequently enough to want to find out what is going on. So, I am letting
      # other exceptions fall through here so that they get reported as bugs in the application instead.
      if oCdbWrapper.uUtilityInterruptThreadId is not None \
        and uThreadId == oCdbWrapper.uUtilityInterruptThreadId \
        and uExceptionCode == STATUS_ACCESS_VIOLATION:
#          assert oCdbWrapper.uUtilityInterruptThreadId is not None, \
#              "An exception 0x%08X happened unexpectedly in the utility process %d/0x%X, thread %d/0x%X: " \
#              "no exception was expected!" % \
#              (uExceptionCode, uProcessId, uProcessId, uThreadId, uThreadId);
#          assert uThreadId == oCdbWrapper.uUtilityInterruptThreadId and uExceptionCode == STATUS_ACCESS_VIOLATION, \
#              "An exception 0x%08X happened unexpectedly in the utility process %d/0x%X, thread %d/0x%X: " \
#              "0x%08X was expected in thread %d/0x%X!" % \
#              (uExceptionCode, uProcessId, uProcessId, uThreadId, uThreadId, \
#              STATUS_ACCESS_VIOLATION, oCdbWrapper.uUtilityInterruptThreadId, oCdbWrapper.uUtilityInterruptThreadId);
        # Terminate the thread in which we triggered an AV, so the utility process can continue running.
        assert fbTerminateThreadForId(oCdbWrapper.uUtilityInterruptThreadId), \
            "Cannot terminate utility thread in utility process";
        # Mark the interrupt as handled.
        oCdbWrapper.uUtilityInterruptThreadId = None;
        # Make sure all threads in all process of the application are resumed, as they were suspended by the
        # cCdbWrapper.fInterruptApplication call.
        auProcessIdsThatNeedToBeResumed.extend(oCdbWrapper.doProcess_by_uId.keys());
        continue;
    # If the application was not suspended on purpose to attach to another process, report it:
    if bCdbHasAttachedToApplication:
      if uBreakpointId is not None:
        sReason = "breakpoint hit";
      elif uExceptionCode is not None:
        sReason = "%s chance exception 0x%08X" % (sChance, uExceptionCode);
      elif sCreateExitProcess == "Create":
        sReason = "new process";
      else:
        sReason = "process terminated";
      oCdbWrapper.fbFireEvent("Application suspended", sReason);
    ### See if it was a debugger break-in for a new process that failed to load properly #############################
    if uExceptionCode == STATUS_WAKE_SYSTEM_DEBUGGER:
      # This exception does not always get reported for the new process; see if there are any processes known to cdb
      # that we do not yet know about:
      asListProcesses = oCdbWrapper.fasExecuteCdbCommand(
        sCommand = "|;",
        sComment = "List processes being debugged",
        bRetryOnTruncatedOutput = True,
      );
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
      oCdbWrapper.oCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId] = cProcess(oCdbWrapper, uProcessId);
      assert oCdbWrapper.oCurrentProcess.uId == uProcessId, \
          "Expected the current process to be %d/0x%X but got %d/0x%X" % \
          (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.uId, oCdbWrapper.oCurrentProcess.uId);
      # Make it a main process too if we're still attaching to or starting the application
      if oCdbWrapper.auProcessIdsPendingAttach:
        uPendingAttachProcessId = oCdbWrapper.auProcessIdsPendingAttach.pop(0);
        assert uPendingAttachProcessId == uProcessId, \
            "Expected to attach to process %d, got %d" % (uPendingAttachProcessId, uProcessId);
      if not bCdbHasAttachedToApplication:
        oCdbWrapper.aoMainProcesses.append(oCdbWrapper.oCurrentProcess);
        # If we are attaching to processes, the current process should be the last one we tried to attach to:
        if oCdbWrapper.auProcessIdsPendingAttach:
          oCdbWrapper.fLogMessageInReport(
            "LogProcess",
            "Attached to process %d/0x%X (%s)." % (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName),
          );
        else:
          oCdbWrapper.fLogMessageInReport(
            "LogProcess",
            "Started process %d/0x%X (%s)." % (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName),
          );
        oCdbWrapper.fbFireEvent("Attached to process", oCdbWrapper.oCurrentProcess);
      else:
        oCdbWrapper.fLogMessageInReport(
          "LogProcess",
          "New process %d/0x%X (%s)." % (uProcessId, uProcessId, oCdbWrapper.oCurrentProcess.sBinaryName),
        );
        oCdbWrapper.fbFireEvent("Started process", oCdbWrapper.oCurrentProcess);
      # If we have a JobObject, add this process to it.
      if oJobObject and not oJobObject.fbAddProcessForId(uProcessId):
        if not bFailedToApplyApplicationMemoryLimitsEventFired:
          # The limits no longer affect the application after the first time this happens, so it is only reported once.
          bFailedToApplyApplicationMemoryLimitsEventFired = True;
          oCdbWrapper.fbFireEvent("Failed to apply application memory limits", oCdbWrapper.oCurrentProcess);
        oCdbWrapper.fbFireEvent("Failed to apply process memory limits", oCdbWrapper.oCurrentProcess);
      # Make sure child processes of the new process are debugged as well.
      oCdbWrapper.fasExecuteCdbCommand(
        sCommand = ".childdbg 1;",
        sComment = "Debug child processes",
        bRetryOnTruncatedOutput = True
      );
      if sCreateExitProcess == "Create":
        # If the application creates a new process, a STATUS_BREAKPOINT exception may follow that signals the
        # same event; this exception should be ignored as we have already handled the new process.
        # This is potentially unreliable: if this exception is not thrown, but the process does trigger a
        # breakpoint for some other reason, it will be ignored. However, I have never seen that happen.
        dauIgnoreNextExceptionCodes_by_uProcessId[uProcessId] = [STATUS_BREAKPOINT];
      else:
        assert uExceptionCode == STATUS_BREAKPOINT, \
            "Expected this to be a debug breakpoint because the debugger attached to a new process";
      # And a STATUS_BREAKPOINT triggered to report a new process in turn can be followed by a STATUS_WX86_BREAKPOINT
      # on x64 systems running a x86 process.
      if oCdbWrapper.sCdbISA == "x64" and oCdbWrapper.oCurrentProcess.sISA == "x86":
        dauIgnoreNextExceptionCodes_by_uProcessId.setdefault(uProcessId, []).append(STATUS_WX86_BREAKPOINT);
      continue;
    else:
      oCdbWrapper.oCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
    if oCdbWrapper.oCurrentProcess.sISA != oCdbWrapper.sCdbISA:
      oCdbWrapper.fasExecuteCdbCommand(
        sCommand = ".effmach %s;" % {"x86": "x86", "x64": "amd64"}[oCdbWrapper.oCurrentProcess.sISA],
        sComment = "Switch to recent event ISA",
        bRetryOnTruncatedOutput = True
      );
      
    ### See if this was an ignored exception #########################################################################
    if uExceptionCode is not None:
      auIgnoreNextExceptionCodes = dauIgnoreNextExceptionCodes_by_uProcessId.get(uProcessId);
      if auIgnoreNextExceptionCodes:
        if uExceptionCode == auIgnoreNextExceptionCodes[0]:
# I used to treat failing ^^^^^^ this test as an error, but now I let the code continue as the exceptions I saw
# indicated that they may truely be bugs in the application. Letting the code continue gets me a bug report to check.
#            assert uExceptionCode == auIgnoreNextExceptionCodes[0], \
#                "Expected to see exception 0x%X in %s process %d/0x%X, but got 0x%X!?" % \
#                (auIgnoreNextExceptionCodes[0], oCdbWrapper.oCurrentProcess.sBinaryName, 
#                oCdbWrapper.oCurrentProcess.uId, oCdbWrapper.oCurrentProcess.uId, uExceptionCode);        
          auIgnoreNextExceptionCodes.pop(0);
          # If there are no more exceptions to be ignored for this process, stop ignoring exceptions.
          if len(auIgnoreNextExceptionCodes) == 0:
            del dauIgnoreNextExceptionCodes_by_uProcessId[uProcessId];
          bLastExceptionWasIgnored = True;
          continue;
    ### Handle process termination ###################################################################################
    if sCreateExitProcess == "Exit":
      assert bCdbHasAttachedToApplication, \
          "No processes are expected to terminated before cdb has fully attached to the application!";
      # A process was terminated. This may be the first time we hear of the process, i.e. the code above may have only
      # just added the process. I do not know why cdb did not throw an event when it was created: maybe it terminated
      # while being created due to some error? Anyway, having added the process in the above code, we'll now mark it as
      # terminated:
      oCdbWrapper.oCurrentProcess.bTerminated = True;
      oCdbWrapper.fbFireEvent("Process terminated", oCdbWrapper.oCurrentProcess);
      bIsMainProcess = oCdbWrapper.oCurrentProcess in oCdbWrapper.aoMainProcesses;
      oCdbWrapper.fLogMessageInReport(
        "LogProcess",
        "Terminated %sprocess %d/0x%X." % (bIsMainProcess and "main " or "", uProcessId, uProcessId),
      );
      # If we have console stdin/stdout/stderr pipes, close them:
      oConsoleProcess = oCdbWrapper.doConsoleProcess_by_uId.get(uProcessId);
      if oConsoleProcess:
        del oCdbWrapper.doConsoleProcess_by_uId[uProcessId];
        # Unfortunately, the console process still exists, but it is suspended. For unknown reasons, attempting to
        # close the handles now will hang until the process is resumed. Since this will not happen unless we continue
        # and let cdb resume, this causes a deadlock. To avoid this we will start another thread that will close the
        # handles. It will hang until we've resumed cdb (or terminated, whatever comes first).
        oCdbWrapper.foHelperThread(oConsoleProcess.fClose).start();
      # This event was explicitly to notify us of the terminated process; no more processing is needed.
      continue;
    assert bCdbHasAttachedToApplication, \
        "No exceptions are expected before cdb has fully attached to the application!";
    ### Handle hit breakpoint ########################################################################################
    if uBreakpointId is not None:
      # A breakpoint was hit; fire the callback
      oCdbWrapper.fLogMessageInReport(
        "LogBreakpoint",
        "The application hit breakpoint #%d." % uBreakpointId,
      );
      fBreakpointCallback = oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
      fBreakpointCallback(uBreakpointId);
      continue;
    ### Free reserve memory for exception analysis ###################################################################
    if oReservedMemoryVirtualAllocation:
      oReservedMemoryVirtualAllocation.fFree();
      oReservedMemoryVirtualAllocation = None;
    ### Analyze potential bugs #######################################################################################
    ### Triggering a breakpoint may indicate a third-party component reported a bug in stdout/stderr; look for that.
    oBugReport = None;
    if uExceptionCode in [STATUS_BREAKPOINT, STATUS_WX86_BREAKPOINT]:
      ### Handle errors reported in stdout/stderr ######################################################################
      oBugReport = (
        foDetectAndCreateBugReportForVERIFIER_STOP(oCdbWrapper, uExceptionCode, asUnprocessedCdbOutput)
        or foDetectAndCreateBugReportForASan(oCdbWrapper, uExceptionCode)
      );
      if oBugReport:
        oCdbWrapper.bFatalBugDetected = True;
        asUnprocessedCdbOutput = [];
    if not oBugReport: 
      # Check if this exception is considered a bug:
      oBugReport = cBugReport.foCreateForException(oCdbWrapper.oCurrentProcess, uExceptionCode, sExceptionDescription, bApplicationCannotHandleException);
    if oBugReport:
      # ...if it is, report it:
      oBugReport.fReport(oCdbWrapper);
      # If we cannot "handle" this bug, this is fatal:
      oCdbWrapper.bFatalBugDetected = not oCdbWrapper.oCollateralBugHandler.fbHandleException();
    else:
      # This exception is not a bug, do not hide it from the application.
      bHideLastExceptionFromApplication = False;
  # Terminate cdb.
  oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = "q",
    sComment = "Terminate cdb",
    bIgnoreOutput = True,
    bUseMarkers = False
  );
  # Wait for cdb to truely terminate
  oCdbWrapper.oCdbProcess.wait();
