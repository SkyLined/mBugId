import datetime, re, time;
from .cBugReport import cBugReport;
from .cException import cException;
from .cProcess import cProcess;
from .dxConfig import dxConfig;

from mWindowsAPI import cJobObject, fbResumeForThreadId, fbTerminateForThreadId, cVirtualAllocation, \
    fStopDebuggingForProcessId;

from mWindowsSDK import *;

def fnGetDebuggerTimeInSeconds(sDebuggerTime):
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

def cCdbWrapper_fCdbStdInOutHelperThread(oCdbWrapper):
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
  # There are many exception that are handled by BugId and which should be hidden by the debugger from the application.
  # This boolean is set to True to indicate this, or False if the exception should be handled by application.
  bHideLastExceptionFromApplication = True; # The first exception is the initial breakpoint, which we hide
  # Create a list of commands to set up event handling.
  
  # Read the initial cdb output related to starting/attaching to the first process.
  oCdbWrapper.fasReadOutput();
  # Turn off prompt information as it is not useful most of the time, but can clutter output and slow down
  # debugging by loading and resolving symbols.
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".prompt_allow -dis -ea -reg -src -sym;",
    sComment = "Display only the prompt",
  );
  # Make sure the cdb prompt is on a new line after the application has been run:
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = '.pcmd -s ".printf \\"\\\\r\\\\n\\";";',
    sComment = "Output a CRLF after running the application",
  );
  auProcessIdsThatNeedToBeResumed = [];
  # We start a utility process in which we can trigger breakpoints to distinguish them from breakpoints in the
  # target application.
  # When a new process is created, stdout/stderr reading threads are created. These will not stop reading when the
  # process terminates, so we need to close these handles when it does. In order to do that we track them here:
  # An bug report will be created when needed; it is returned at the end
  oBugReport = None;
  while ( # run this loop while...
    # ... we still need to start the application ...
    not oCdbWrapper.bApplicationStarted
    # ... or we still need to attach to processes ...
    or len(oCdbWrapper.auProcessIdsPendingAttach) > 0 
    # ... or there is at least one process running for the application ...
    or len([oProcess for oProcess in oCdbWrapper.doProcess_by_uId.values() if not oProcess.bTerminated]) >= 1
  ):
    if oCdbWrapper.uUtilityProcessId is not None:
      oCdbWrapper.fRunTimeoutCallbacks();
      ### Attaching to or starting application #######################################################################
      if not oCdbWrapper.bApplicationStarted:
        if oCdbWrapper.oUWPApplication:
          assert not oCdbWrapper.bUWPApplicationStarted, \
              "The UWP application should not be started twice; something has gone wrong.";
          if len(oCdbWrapper.asApplicationArguments) == 0:
            sArgument = None;
          else:
            # This check should be superfluous, but it doesn't hurt to make sure.
            assert len(oCdbWrapper.asApplicationArguments) == 1, \
                "Expected exactly one argument";
            sArgument = oCdbWrapper.asApplicationArguments[0];
          oCdbWrapper.fTerminateUWPApplication(oCdbWrapper.oUWPApplication);
          oCdbWrapper.fStartUWPApplication(oCdbWrapper.oUWPApplication, sArgument);
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
      # There will no longer be a current process or thread.
      oCdbWrapper.oCdbCurrentProcess = None;
      oCdbWrapper.oCdbCurrentWindowsAPIThread = None;
      ### Allocate reserve memory ####################################################################################
      # Reserve some memory for exception analysis in case the target application causes a system-wide low-memory
      # situation.
      if dxConfig["uReservedMemory"]:
        if oReservedMemoryVirtualAllocation is None:
          try:
            oReservedMemoryVirtualAllocation = cVirtualAllocation.foCreateForProcessId(
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
      oCdbWrapper.oApplicationTimeLock.fAcquire();
      try:
        oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds = fnGetDebuggerTimeInSeconds(oTimeMatch.group(1));
        oCdbWrapper.nApplicationResumeTimeInSeconds = time.clock();
      finally:
        oCdbWrapper.oApplicationTimeLock.fRelease();
      ### Resume application #########################################################################################
      if oCdbWrapper.bStopping: break; # Unless we have been requested to stop.
      asOutputWhileRunningApplication = oCdbWrapper.fasExecuteCdbCommand(
        sCommand = "g%s;" % (bHideLastExceptionFromApplication and "h" or "n"),
        sComment = "Running application",
        bOutputIsInformative = True,
        bApplicationWillBeRun = True, # This command will cause the application to run.
        bUseMarkers = False, # This does not work with g commands: the end marker will never be shown.
      );
      # We will assume this exception will be handled by BugId and set bHideLastExceptionFromApplication to True to
      # hide it from the application. If the application should see and handle this exception, we will set
      # bHideLastExceptionFromApplication to False later
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
      "^(?:%s)$" % "".join([
        r"Last event: (?:",
          r"<no event>",  # This means the application send debug output
        r"|",
          r"([0-9a-f]+)\.([0-9a-f]+): ",
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
        r")",
      ]),
      asCleanedLastEventOutput[0],
      re.I
    );
    assert oEventMatch, "Invalid .lastevent output on line #1:\r\n%s" % "\r\n".join(asLastEventOutput);
    oEventTimeMatch = re.match(r"^\s*debugger time: (.*?)\s*$", asCleanedLastEventOutput[1]);
    assert oEventTimeMatch, "Invalid .lastevent output on line #2:\r\n%s" % "\r\n".join(asLastEventOutput);
    oCdbWrapper.oApplicationTimeLock.fAcquire();
    try:
      if oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds:
        # Add the time between when the application was resumed and when the event happened to the total application
        # run time.
        oCdbWrapper.nConfirmedApplicationRunTimeInSeconds += fnGetDebuggerTimeInSeconds(oEventTimeMatch.group(1)) - oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds;
      # Mark the application as suspended by setting nApplicationResumeDebuggerTimeInSeconds to None.
      oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds = None;
      oCdbWrapper.nApplicationResumeTimeInSeconds = None;
    finally:
      oCdbWrapper.oApplicationTimeLock.fRelease();
    (
      sProcessIdHex, sThreadIdHex,
      sCreateExitProcess, sCreateExitProcessIdHex,
      sIgnoredUnloadModule,
      sExceptionCodeDescription, sExceptionCode, sChance,
      sBreakpointId,
    ) = oEventMatch.groups();
    if not sProcessIdHex:
      # The last event was an application debugger output event.
      uProcessId = oCdbWrapper.fuGetValueForRegister("$tpid", "Get current process id");
      if uProcessId == oCdbWrapper.uUtilityProcessId:
        # Our utility process is not expected to output anything, but since we're using cmd.exe, it might behave in a
        # way that we do not expect: I've seen it output debug messages in low memory situations. It would be best to
        # either suspend it entirely, or replace cmd.exe with a custom binary that does nothing at all. However, it's
        # easier to just ignore these messages, so I'll do that for now:
        continue;
      oCdbWrapper.oCdbCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
      uThreadId = oCdbWrapper.fuGetValueForRegister("$tid", "Get current thread id");
      oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
      if oCdbWrapper.oCdbCurrentProcess.sISA != oCdbWrapper.sCdbCurrentISA:
        # Select process ISA if it is not yet the current ISA. ".block{}" is required
        oCdbWrapper.fasExecuteCdbCommand(
          sCommand = ".effmach %s;" % {"x86": "x86", "x64": "amd64"}[oCdbWrapper.oCdbCurrentProcess.sISA],
          sComment = "Switch to current process ISA",
          bRetryOnTruncatedOutput = True,
        );
        # Assuming there's no error, track the new current isa.
        oCdbWrapper.sCdbCurrentISA = oCdbWrapper.oCdbCurrentProcess.sISA;
      # Unfortunately, cdb outputs text whenever an ignored first chance exception happens and I cannot find out how to
      # silence it. So, we'll have to remove these from the output, which is sub-optimal, but should work well enough
      # for now. Also, page heap outputs stuff that we don't care about as well, which we hide here.
      asDebugOutput = [
        sLine for sLine in asOutputWhileRunningApplication
        if not re.match("^(%s)$" % "|".join([
          r"\(\w+\.\w+\): Unknown exception \- code \w{8} \(first chance\)",
          r"Page heap: pid 0x\w+: page heap enabled with flags 0x\w+\.",
        ]), sLine)
      ];
      if asDebugOutput:
        # It could be that the output was from page heap, in which case no event is fired.
        oCdbWrapper.fbFireEvent("Application debug output", oCdbWrapper.oCdbCurrentProcess, asDebugOutput);
      continue;
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
      # TODO: no exceptions other than the AVs caused deliberately by us are expected. In newer versions of Windows,
      # Control Flow Guard will detect an attempt to call a function at an invalid address and report a
      # STATUS_STACK_BUFFER_OVERRUN instead of triggering an AV.
      # I would like to have an assert here to make sure the exception is either of these, but I found that I do not
      # have enough information to report in the assert to determine the root cause of such unexpected exceptions. So,
      # I am letting other exceptions fall through here so that they get reported as if they were bugs in the
      # application instead... this is not ideal, but should help resolve these issues faster.
#      assert oCdbWrapper.uUtilityInterruptThreadId is not None, \
#          "An exception 0x%08X happened unexpectedly in the utility process %d/0x%X, thread %d/0x%X: " \
#          "no exception was expected!" % \
#          (uExceptionCode, uProcessId, uProcessId, uThreadId, uThreadId);
#      assert uExceptionCode in [STATUS_ACCESS_VIOLATION, STATUS_STACK_BUFFER_OVERRUN], \
#          "An exception 0x%08X happened unexpectedly in the utility process %d/0x%X, thread %d/0x%X: " \
#          "exception 0x%08X or 0x%08X was expected in thread %d/0x%X!" % \
#          (uExceptionCode, uProcessId, uProcessId, uThreadId, uThreadId, \
#          STATUS_ACCESS_VIOLATION, STATUS_STACK_BUFFER_OVERRUN, \
#          oCdbWrapper.uUtilityInterruptThreadId, oCdbWrapper.uUtilityInterruptThreadId);
#      assert uThreadId == oCdbWrapper.uUtilityInterruptThreadId, \
#          "An exception 0x%08X happened unexpectedly in the utility process %d/0x%X, thread %d/0x%X: " \
#          "this exception was expected in thread %d/0x%X!" % \
#          (uExceptionCode, uProcessId, uProcessId, uThreadId, uThreadId, \
#          oCdbWrapper.uUtilityInterruptThreadId, oCdbWrapper.uUtilityInterruptThreadId);
      if (
        uThreadId == oCdbWrapper.uUtilityInterruptThreadId
        and uExceptionCode in [STATUS_ACCESS_VIOLATION, STATUS_STACK_BUFFER_OVERRUN]
      ):
        # Terminate the thread in which we triggered an AV, so the utility process can continue running.
        # Since it is suspended, it will not terminate when we ask it to.
        assert not fbTerminateForThreadId(uThreadId, bWait = False), \
            "Expected thread to still be suspended, but it was terminated";
        # Mark the interrupt as handled.
        oCdbWrapper.uUtilityInterruptThreadId = None;
        oCdbWrapper.fbFireEvent("Log message", "Application interrupted");
        assert bHideLastExceptionFromApplication, \
            "Just making sure we are in a sane state";
        continue;
      if sCreateExitProcess == "Exit":
        # Something terminated the utility process. This can happen if the console we're running in gets closed. We'll
        # ignore it, as all other processes should terminate as well so we will end up exiting cleanly. However, any
        # attempt to use the utility process will fail, so I am using the magic value -1 as the utility process id to
        # identify this situation.
        oCdbWrapper.uUtilityProcessId = -1;
        continue;
      # This is not an expected exception: report it as a bug.
      # We will need to "fake" that the utility process is part of the application, as code expectes to be able to
      # refer to it from doProcess_by_uId:
      oCdbWrapper.doProcess_by_uId[uProcessId] = cProcess(oCdbWrapper, uProcessId);
      oCdbWrapper.fSelectProcess(uProcessId);
    if sCreateExitProcess == "Create":
      if oCdbWrapper.bApplicationStarted:
        oCdbWrapper.fbFireEvent("Application suspended", "Attached to process");
      oCdbWrapper.fHandleNewApplicationProcess(uProcessId);
      continue;
    assert oCdbWrapper.bApplicationStarted, \
        "Unexpected exception before cdb has started the application:\r\n%s" % "\r\n".join(asLastEventOutput);
    if sCreateExitProcess == "Exit":
      oCdbWrapper.fbFireEvent("Application suspended", "Process terminated");
      oCdbWrapper.fHandleApplicationProcessTermination(uProcessId);
      continue;
    if sIgnoredUnloadModule:
      # This exception makes no sense; we never requested it and do not care about it: ignore it.
      continue;
    oCdbWrapper.oCdbCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
    oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
    if oCdbWrapper.oCdbCurrentProcess.sISA != oCdbWrapper.sCdbCurrentISA:
      # Select process ISA if it is not yet the current ISA. ".block{}" is required
      oCdbWrapper.fasExecuteCdbCommand(
        sCommand = ".effmach %s;" % {"x86": "x86", "x64": "amd64"}[oCdbWrapper.oCdbCurrentProcess.sISA],
        sComment = "Switch to current process ISA",
        bRetryOnTruncatedOutput = True,
      );
      # Assuming there's no error, track the new current isa.
      oCdbWrapper.sCdbCurrentISA = oCdbWrapper.oCdbCurrentProcess.sISA;
    oException = uExceptionCode is not None and cException.foCreate(
      oProcess = oCdbWrapper.oCdbCurrentProcess,
      uCode = uExceptionCode,
      sCodeDescription = sExceptionCodeDescription,
      bApplicationCannotHandleException = bApplicationCannotHandleException,
    ) or None;
    if uExceptionCode == STATUS_BREAKPOINT:
      if oException.uAddress in oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId.get(uProcessId, []):
        # cdb appears to trigger int3s after the breakpoints have been removed, which we ignore.
        continue;
      if uProcessId == oCdbWrapper.uUtilityProcessId:
        # cdb can trigger a breakpoint in the utility process, which we remove.
        continue;
      if oException.oFunction and oException.oFunction.sName == "ntdll.dll!DbgBreakPoint" and not bApplicationCannotHandleException:
        # I cannot seem to figure out how to stop cdb from triggering a ntdll!DbgUiRemoteBreakin in new processes. From
        # what I understand, using "sxi ibp" should do the trick but it does not appear to have any effect. I'll try to
        # detect these exceptions from the function in which they are triggered; there is a chance of false positives,
        # but I have not seen any. If we detect one, we ignore it:
        continue;
    ### Free reserve memory for exception analysis ###################################################################
    if oReservedMemoryVirtualAllocation:
      oReservedMemoryVirtualAllocation.fFree();
      oReservedMemoryVirtualAllocation = None;
    ### Handle hit breakpoint ########################################################################################
    if uBreakpointId is not None:
      oCdbWrapper.fbFireEvent("Application suspended", "Breakpoint hit");
      # A breakpoint was hit; sanity checks, log message and fire the callback
      uCurrentProcessId = oCdbWrapper.oCdbCurrentProcess.uId;
      uExpectedProcessId = oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
      assert uCurrentProcessId == uExpectedProcessId, \
          "Breakpoint #%d was set in process %d/0x%X but reported to have been hit in process %d/0x%X" % \
          (uBreakpointId, uExpectedProcessId, uExpectedProcessId, uCurrentProcessId, uCurrentProcessId);
      uBreakpointAddress = oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId];
      # We could sanity check the breakpoint address matched current eip/rip, but I don't have time to implement it and
      # it would slow things down a bit.
      oCdbWrapper.fbFireEvent("Log message", "Breakpoint hit", {
        "Breakpoint id": "%d" % uBreakpointId,
        "Address": "0x%X" % uBreakpointAddress,
      });
      fBreakpointCallback = oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
      fBreakpointCallback(uBreakpointId);
      continue;
    oCdbWrapper.fbFireEvent("Application suspended", "%s chance exception 0x%08X" % (sChance.capitalize(), uExceptionCode));
    ### Analyze potential bugs #######################################################################################
    ### Triggering a breakpoint may indicate a third-party component reported a bug in stdout/stderr; look for that.
    oBugReport = None;
    if not oBugReport: 
      # Check if this exception is considered a bug:
      oBugReport = cBugReport.foCreateForException(
        oCdbWrapper.oCdbCurrentProcess,
        oCdbWrapper.oCdbCurrentWindowsAPIThread,
        oException,
      );
    if oBugReport:
      # ...if it is, report it:
      oBugReport.fReport(oCdbWrapper);
      # If we cannot "handle" this bug, this is fatal:
      if not oCdbWrapper.oCollateralBugHandler.fbTryToIgnoreException():
        break;
    else:
      # This may have been considered a bug long enough to set an exception handler. This exception handler must be
      # removed, as it would otherwise lead to an internal exception when the code tries to set another exception
      # handler when it comes acrosss another exception that it consideres a bug.
      oCdbWrapper.oCollateralBugHandler.fDiscardIgnoreExceptionFunction();
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
