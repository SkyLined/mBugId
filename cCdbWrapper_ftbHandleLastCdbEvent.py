import re;

from mWindowsSDK import fs0GetErrorDefineName, DBG_CONTROL_C, STATUS_BREAKPOINT;

from .cBugReport import cBugReport;
from .cException import cException;
from .cProcess import cProcess;
from .fnGetDebuggerTimeInSeconds import fnGetDebuggerTimeInSeconds;

# Return (bEventIsFatal, bEventHasBeenHandled)
HIDE_EVENT_FROM_APPLICATION = (False, True);
REPORT_EVENT_TO_APPLICATION = (False, False);
STOP_DEBUGGING = (True, False);
def cCdbWrapper_ftbHandleLastCdbEvent(oCdbWrapper, asOutputWhileRunningApplication):
  ### Get information about the last event that caused cdb to pause execution ########################################
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
  assert len(asCleanedLastEventOutput) == 2, \
    "Invalid .lastevent output:\r\n%s" % "\r\n".join(asLastEventOutput);
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
  assert oEventMatch, \
    "Invalid .lastevent output on line #1:\r\n%s" % "\r\n".join(asLastEventOutput);
  (
    s0ProcessIdHex, s0ThreadIdHex,
    s0CreateExitProcess, s0CreateExitProcessIdHex,
    sIgnoredUnloadModule,
    s0ExceptionCodeDescription, s0ExceptionCode, sChance,
    s0BreakpointId,
  ) = oEventMatch.groups();
  
  ### Parse information about application execution time #############################################################
  oEventTimeMatch = re.match(r"^\s*debugger time: (.*?)\s*$", asCleanedLastEventOutput[1]);
  assert oEventTimeMatch, \
    "Invalid .lastevent output on line #2:\r\n%s" % "\r\n".join(asLastEventOutput);
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
  
  if sIgnoredUnloadModule:              # Unload module event: we never requested this; ignore.
    return HIDE_EVENT_FROM_APPLICATION;
  
  ### Parse information about the process and thread or get it if not provided #######################################
  # If the event provides a process and thread id, use those. Otherwise ask cdb about the current process and thread.
  if s0ProcessIdHex:
    uProcessId = long(s0ProcessIdHex, 16);
    uThreadId = long(s0ThreadIdHex, 16);
  else:
    uProcessId = oCdbWrapper.fuGetValueForRegister("$tpid", "Get current process id");
    uThreadId = oCdbWrapper.fuGetValueForRegister("$tid", "Get current thread id");
  
  ### Select the right process and thread and detect new processes #################################################
  # Sets `oCdbCurrentProcess`, `oCdbCurrentWindowsAPIThread`, and `sCdbCurrentISA`
  oCdbWrapper.oCdbCurrentProcess = oCdbWrapper.doProcess_by_uId.get(uProcessId);
  bNewProcess = oCdbWrapper.oCdbCurrentProcess is None;
  bAttachedToProcess = bNewProcess and oCdbWrapper.auProcessIdsPendingAttach and uProcessId == oCdbWrapper.auProcessIdsPendingAttach[0];
  if bNewProcess:
    # Create a new process object and make it the current process.
    oCdbWrapper.oCdbCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId] = cProcess(oCdbWrapper, uProcessId);
    if bAttachedToProcess:
      oCdbWrapper.auProcessIdsPendingAttach.pop(0);
  oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
  oCdbWrapper.fUpdateCdbISA();
  ### Handle new processes ##########################################################################################
  if bNewProcess:
    if uProcessId == oCdbWrapper.oUtilityProcess.uId:
      oCdbWrapper.fHandleAttachedToUtilityProcess();
    else:
      oCdbWrapper.fHandleAttachedToApplicationProcess();
  
  ### Handle non-exception events ####################################################################################
  if not s0ProcessIdHex:                # Application debug output events: handle.
    oCdbWrapper.fbFireCallbacks("Application suspended", "Application debug output");
    oCdbWrapper.fHandleDebugOutputFromApplication(asOutputWhileRunningApplication);
    return HIDE_EVENT_FROM_APPLICATION;
  if s0BreakpointId is not None:        # Application hit a breakpoint events: handle.
    oCdbWrapper.fbFireCallbacks("Application suspended", "Breakpoint hit");
    oCdbWrapper.fHandleBreakpoint(long(s0BreakpointId));
    return HIDE_EVENT_FROM_APPLICATION;
  if s0CreateExitProcess == "Create":   # Create process events: already handled.
    oCdbWrapper.fbFireCallbacks("Application suspended", "New process created");
    assert s0CreateExitProcessIdHex == s0ProcessIdHex, \
      "s0CreateExitProcessIdHex (%s) is expected to be s0ProcessIdHex (%s)" % (s0CreateExitProcessIdHex, s0ProcessIdHex);
    return HIDE_EVENT_FROM_APPLICATION;
  if s0CreateExitProcess == "Exit":     # Exit process events: handle.
    oCdbWrapper.fbFireCallbacks("Application suspended", "Process terminated");
    assert s0CreateExitProcessIdHex == s0ProcessIdHex, \
      "s0CreateExitProcessIdHex (%s) is expected to be s0ProcessIdHex (%s)" % (s0CreateExitProcessIdHex, s0ProcessIdHex);
    assert uProcessId != oCdbWrapper.oUtilityProcess.uId, \
        "The utility process has terminated unexpectedly!";
    oCdbWrapper.fHandleCurrentApplicationProcessTermination();
    return HIDE_EVENT_FROM_APPLICATION;
  
  ### Handle exceptions ##############################################################################################
  uExceptionCode = long(s0ExceptionCode, 16);
  sRelatedErrorDefineName = fs0GetErrorDefineName(uExceptionCode) or "unknown exception";
  oCdbWrapper.fbFireCallbacks("Application suspended", "%s chance exception 0x%08X (%s)" % (sChance.capitalize(), uExceptionCode, sRelatedErrorDefineName));

  # Handle user pressing CTRL+C
  if uExceptionCode == DBG_CONTROL_C:  # User pressed CTRL+C event: terminate.
    oCdbWrapper.fbFireCallbacks("Application suspended", "User pressed CTRL+C");
    oCdbWrapper.fbFireCallbacks("Log message", "User pressed CTRL+C");
    return HIDE_EVENT_FROM_APPLICATION;
  # Handle exceptions in utility process.
  if uProcessId == oCdbWrapper.oUtilityProcess.uId: # Exception in utility process: handle.
    if uExceptionCode != STATUS_BREAKPOINT or not bAttachedToProcess:
      # This is not a breakpoint triggered because we attached to the utilityprocess.
      oCdbWrapper.fHandleExceptionInUtilityProcess(uExceptionCode, sRelatedErrorDefineName);
    return HIDE_EVENT_FROM_APPLICATION;
  
  bApplicationCannotHandleException = sChance == "second";
  oException = cException.foCreate(
    oProcess = oCdbWrapper.oCdbCurrentProcess,
    uCode = uExceptionCode,
    sCodeDescription = s0ExceptionCodeDescription,
    bApplicationCannotHandleException = bApplicationCannotHandleException,
  );
  if uExceptionCode == STATUS_BREAKPOINT and oException.uAddress in oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId.get(uProcessId, []):
    # cdb appears to trigger int3s after the breakpoints have been removed, which we ignore.
    return HIDE_EVENT_FROM_APPLICATION;
  if (
    uExceptionCode == STATUS_BREAKPOINT
    and not bApplicationCannotHandleException
    and oException.oFunction
    and oException.oFunction.sName == "ntdll.dll!DbgBreakPoint"
  ):
    # I cannot seem to figure out how to stop cdb from triggering a ntdll!DbgUiRemoteBreakin in new processes. From
    # what I understand, using "sxi ibp" should do the trick but it does not appear to have any effect. I'll try to
    # detect these exceptions from the function in which they are triggered; there is a chance of false positives,
    # but I have not seen any. If we detect one, we ignore it:
    return HIDE_EVENT_FROM_APPLICATION;
  
  ### Analyze potential bugs #########################################################################################
  # Free reserve memory before exception analysis
  if oCdbWrapper.oReservedMemoryVirtualAllocation:
    oCdbWrapper.oReservedMemoryVirtualAllocation.fFree();
    oCdbWrapper.oReservedMemoryVirtualAllocation = None;
  o0BugReport = cBugReport.fo0CreateForException(
    oCdbWrapper.oCdbCurrentProcess,
    oCdbWrapper.oCdbCurrentWindowsAPIThread,
    oException,
  );
  if not o0BugReport:
    # This is not considered a bug; continue execution
    # This may have been tentatively considered a bug at some point and the collateral bug handler may have set an
    # exception handler. This exception handler must be removed, as it would otherwise lead to an internal exception
    # if the code later tries to set another exception handler.
    oCdbWrapper.oCollateralBugHandler.fDiscardIgnoreExceptionFunction();
    return REPORT_EVENT_TO_APPLICATION;

  ### Report bug and see if the collateral bug handler can ignore it #################################################
  o0BugReport.fReport(oCdbWrapper);
  # If we cannot ignore this bug, stop execution:
  if not oCdbWrapper.oCollateralBugHandler.fbTryToIgnoreException():
    return STOP_DEBUGGING;
  # Collateral bug handler has handled this event; hide it from the application.
  return HIDE_EVENT_FROM_APPLICATION;

