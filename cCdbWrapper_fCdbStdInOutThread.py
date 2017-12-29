import datetime, re, time;
from cBugReport import cBugReport;
from cCdbStoppedException import cCdbStoppedException;
from cProcess import cProcess;
from dxConfig import dxConfig;
from foDetectAndCreateBugReportForVERIFIER_STOP import foDetectAndCreateBugReportForVERIFIER_STOP;
from foDetectAndCreateBugReportForASan import foDetectAndCreateBugReportForASan;
from mWindowsAPI import cJobObject, fbTerminateThreadForId, cVirtualAllocation, cConsoleProcess, fResumeProcessForId, \
    fsGetProcessISAForId, fbTerminateProcessForId, fStopDebuggingProcessForId;

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
    oCdbWrapper.oJobObject = cJobObject();
    if oCdbWrapper.uProcessMaxMemoryUse is not None:
      oCdbWrapper.oJobObject.fSetMaxProcessMemoryUse(oCdbWrapper.uProcessMaxMemoryUse);
    if oCdbWrapper.uTotalMaxMemoryUse is not None:
      oCdbWrapper.oJobObject.fSetMaxTotalMemoryUse(oCdbWrapper.uTotalMaxMemoryUse);
  else:
    oCdbWrapper.oJobObject = None;
  # If we cannot apply memory limits, we'll fire an event. This should be done only once.
  oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired = True;
  # We may want to reserve some memory, which we'll track using this variable
  oReservedMemoryVirtualAllocation = None;
  # There are situations where an exception should be handled by the debugger and not by the application, this
  # boolean is set to True to indicate this and is used to execute either "gh" or "gn" in cdb.
  bHideLastExceptionFromApplication = False;
  # Create a list of commands to set up event handling.
  
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
          oCdbWrapper.fbFireEvent("Log message", "Terminating UWP application", {
            "Application Id": oCdbWrapper.oUWPApplication.sApplicationId, 
            "Package name": oCdbWrapper.oUWPApplication.sPackageName, 
            "Package full name": oCdbWrapper.oUWPApplication.sPackageFullName, 
          });
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
            oCdbWrapper.fbFireEvent("Log message", "Starting UWP application", {
              "Application Id": oCdbWrapper.oUWPApplication.sApplicationId, 
              "Package name": oCdbWrapper.oUWPApplication.sPackageName, 
              "Package full name": oCdbWrapper.oUWPApplication.sPackageFullName, 
            });
          else:
            # This check should be superfluous, but it doesn't hurt to make sure.
            assert len(oCdbWrapper.asApplicationArguments) == 1, \
                "Expected exactly one argument";
            # Note that the space between the argument and the command-terminating semi-colon MUST be there to make
            # sure the semi-colon is not passed to the UWP app as part of the argument!
            sStartUWPApplicationCommand = ".createpackageapp %s %s %s ;" % \
                (oCdbWrapper.oUWPApplication.sPackageFullName, oCdbWrapper.oUWPApplication.sApplicationId, oCdbWrapper.asApplicationArguments[0]);
            oCdbWrapper.fbFireEvent("Log message", "Starting UWP application", {
              "Application Id": oCdbWrapper.oUWPApplication.sApplicationId, 
              "Package name": oCdbWrapper.oUWPApplication.sPackageName, 
              "Package full name": oCdbWrapper.oUWPApplication.sPackageFullName, 
              "Argument": oCdbWrapper.asApplicationArguments[0],
            });
          asStartUWPApplicationOutput = oCdbWrapper.fasExecuteCdbCommand(
            sCommand = sStartUWPApplicationCommand,
            sComment = "Start UWP application %s" % oCdbWrapper.oUWPApplication.sPackageName,
          );
          assert asStartUWPApplicationOutput == ["Attach will occur on next execution"], \
              "Unexpected .createpackageapp output: %s" % repr(asStartUWPApplicationOutput);
        else:
          oCdbWrapper.fbFireEvent("Log message", "Starting application", {
            "Binary path": oCdbWrapper.sApplicationBinaryPath, 
            "Arguments": " ".join([
              " " in sArgument and '"%s"' % sArgument.replace('"', r'\"') or sArgument
              for sArgument in oCdbWrapper.asApplicationArguments
            ]),
          });
          oConsoleProcess = cConsoleProcess.foCreateForBinaryPathAndArguments(
            sBinaryPath = oCdbWrapper.sApplicationBinaryPath,
            asArguments = oCdbWrapper.asApplicationArguments,
            bRedirectStdIn = False,
            bSuspended = True,
            bDebug = True,
          );
          if oConsoleProcess is None:
            sMessage = "Unable to start a new process for binary \"%s\"." % oCdbWrapper.sApplicationBinaryPath;
            assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
                sMessage;
            break;
          # Start and stop debugging it; but if we do not, VERIFIER STOPs will throw a debugger breakpoint by creating a new
          # thread and calling ntdll!DebugBreak in it. In that situation, we cannot get the stack of the call that caused the
          # VERIFIER STOP, as we do not know in which thread it was. However, by calling these two functions below, we can get
          # VERIFIER STOPs to throw a debugger breakpoint immediately, so we can get a stack. At least, that is the theory...
          fStopDebuggingProcessForId(oConsoleProcess.uId);
          oCdbWrapper.doConsoleProcess_by_uId[oConsoleProcess.uId] = oConsoleProcess;
          # a 32-bit debugger cannot debug 64-bit processes. Report this.
          if oCdbWrapper.sCdbISA == "x86":
            if fsGetProcessISAForId(oConsoleProcess.uId) == "x64":
              assert oConsoleProcess.fbTerminate(5), \
                  "Failed to terminate process %d/0x%X within 5 seconds" % \
                  (oConsoleProcess.uId, oConsoleProcess.uId);
              sMessage = "Unable to debug a 64-bit process using 32-bit cdb.";
              assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
                  sMessage;
              oCdbWrapper.fTerminate();
              return;
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
          oCdbWrapper.fbFireEvent("Log message", "Attaching to application", {
            "Process": "%d/0x%X" % (oConsoleProcess.uId, oConsoleProcess.uId),
            "Binary path": oCdbWrapper.sApplicationBinaryPath, 
            "Arguments": " ".join([
              " " in sArgument and '"%s"' % sArgument.replace('"', r'\"') or sArgument
              for sArgument in oCdbWrapper.asApplicationArguments
            ]),
          });
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
          oCdbWrapper.fbFireEvent("Log message", "Resuming all threads in process", {
            "Process id": "%d/0x%X" % (uProcessId, uProcessId), 
          });
# This does not appear to work :(
#          fResumeProcessForId(uProcessId);
# But this does:
          oCdbWrapper.fSelectProcess(uProcessId);
          oCdbWrapper.fasExecuteCdbCommand(
            sCommand = "~*m",
            sComment = "Resume threads for process %d/0x%X" % (uProcessId, uProcessId),
          );
      ### Check if page heap is enabled in all processes and discard cached info #####################################
      if dxConfig["bEnsurePageHeap"]:
        for uProcessId, oProcess in oCdbWrapper.doProcess_by_uId.items():
          if not oProcess.bTerminated:
            oProcess.fEnsurePageHeapIsEnabled();
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
              uProcessId = oCdbWrapper.oCdbConsoleProcess.uId,
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
    asCleanedLastEventOutput = [s for s in asLastEventOutput if s]; # Remove empty lines
    assert len(asCleanedLastEventOutput) == 2, "Invalid .lastevent output:\r\n%s" % "\r\n".join(asLastEventOutput);
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
      asCleanedLastEventOutput[0],
      re.I
    );
    assert oEventMatch, "Invalid .lastevent output on line #1:\r\n%s" % "\r\n".join(asLastEventOutput);
    oEventTimeMatch = re.match(r"^\s*debugger time: (.*?)\s*$", asCleanedLastEventOutput[1]);
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
    uProcessId = long(sProcessIdHex, 16);
    uThreadId = long(sThreadIdHex, 16);
    uExceptionCode = sExceptionCode and long(sExceptionCode, 16);
    bApplicationCannotHandleException = sChance == "second";
    uBreakpointId = sBreakpointId and long(sBreakpointId);
    assert not sCreateExitProcessIdHex or sProcessIdHex == sCreateExitProcessIdHex, \
        "This is highly unexpected";
    # Handle new processes being started
    if oCdbWrapper.uUtilityProcessId is None:
      assert uExceptionCode == STATUS_BREAKPOINT, \
          "An unexpected event happened before cdb.exe reported that the utility process was loaded: %s" % \
          repr(asLastEventOutput);
      oCdbWrapper.fHandleNewUtilityProcess(uProcessId);
      continue;
    # Handle exceptions in the utility process
    if uProcessId == oCdbWrapper.uUtilityProcessId:
      # TODO: no exceptions other than the AVs caused deliberately by us are expected. I would like to have an assert
      # here, but I found that this happened frequently enough to want to find out what is going on. So, I am letting
      # other exceptions fall through here so that they get reported as bugs in the application instead.
      if oCdbWrapper.uUtilityInterruptThreadId is not None:
        if uThreadId == oCdbWrapper.uUtilityInterruptThreadId \
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
        oCdbWrapper.fbFireEvent("Log message", "Application interrupted");
        continue;
    if sCreateExitProcess == "Create":
      bIsMainProcess = not bCdbHasAttachedToApplication;
      if not bIsMainProcess:
        oCdbWrapper.fbFireEvent("Application suspended", "Attached to process");
      oCdbWrapper.fHandleNewApplicationProcess(uProcessId, bIsMainProcess);
      continue;
    assert bCdbHasAttachedToApplication, \
        "Unexpected exception before cdb has fully attached to the application:\r\n%s" % "\r\n".join(asLastEventOutput);
    if sIgnoredUnloadModule:
      # This exception makes no sense; we never requested it and do not care about it: ignore it.
      bLastExceptionWasIgnored = True;
      continue;
    if sCreateExitProcess == "Exit":
      oCdbWrapper.fbFireEvent("Application suspended", "Process terminated");
      oCdbWrapper.fHandleApplicationProcessTermination(uProcessId);
      continue;
    oCdbWrapper.oCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
    ### Free reserve memory for exception analysis ###################################################################
    if oReservedMemoryVirtualAllocation:
      oReservedMemoryVirtualAllocation.fFree();
      oReservedMemoryVirtualAllocation = None;
# I believe this is no longer needed.
#    ### See if it was a debugger break-in for a new process that failed to load properly #############################
#    if uExceptionCode == STATUS_WAKE_SYSTEM_DEBUGGER:
#      # This exception does not always get reported for the new process; see if there are any processes known to cdb
#      # that we do not yet know about:
#      asListProcesses = oCdbWrapper.fasExecuteCdbCommand(
#        sCommand = "|;",
#        sComment = "List processes being debugged",
#        bRetryOnTruncatedOutput = True,
#      );
#      auNewProcessIds = [];
#      for sListProcess in asListProcesses:
#        oProcessIdMatch = re.match("[#\.\s]+\d+\s+id:\s+([0-9a-f]+)\s+.*", sListProcess, re.I);
#        assert oProcessIdMatch, \
#            "Unrecognized process list output: %s\r\n%s" % (repr(sListProcess), "\r\n".join(asListProcesses));
#        uPotentiallNewProcessId = long(oProcessIdMatch.group(1), 16);
#        if uPotentiallNewProcessId not in oCdbWrapper.doProcess_by_uId:
#          auNewProcessIds.append(uPotentiallNewProcessId);
#      #  We're expecting there to be at most 1:
#      assert len(auNewProcessIds) < 2, \
#          "Found %d new processes: %s" % (len(auNewProcessIds), ", ".join([str(u) for u in auNewProcessIds]));
#      if len(auNewProcessIds) == 1:
#        # This process is new, handle it.
#        uProcessId = auNewProcessIds[0];
    # Make sure cdb switches to the right ISA for the current process.
    if oCdbWrapper.oCurrentProcess.sISA != oCdbWrapper.sCdbISA:
      oCdbWrapper.fasExecuteCdbCommand(
        sCommand = ".effmach %s;" % {"x86": "x86", "x64": "amd64"}[oCdbWrapper.oCurrentProcess.sISA],
        sComment = "Switch to current process ISA",
        bRetryOnTruncatedOutput = True,
      );
    ### Handle hit breakpoint ########################################################################################
    if uBreakpointId is not None:
      oCdbWrapper.fbFireEvent("Application suspended", "Breakpoint hit");
      # A breakpoint was hit; fire the callback
      oCdbWrapper.fbFireEvent("Log message", "Breakpoint hit", {
        "Breakpoint id": "%d" % uBreakpointId,
      });
      fBreakpointCallback = oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
      fBreakpointCallback(uBreakpointId);
      continue;
    oCdbWrapper.fbFireEvent("Application suspended", "%s chance exception 0x%08X" % (sChance.capitalize(), uExceptionCode));
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
  oCdbWrapper.fbFireEvent("Log message", "Terminating cdb.exe");
  oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = "q",
    sComment = "Terminate cdb",
    bIgnoreOutput = True,
    bUseMarkers = False
  );
  # The above should raise a cCdbTerminedException, so the below should not be reached.
  raise AssertionError("Cdb failed to terminate after sending 'q' command");
