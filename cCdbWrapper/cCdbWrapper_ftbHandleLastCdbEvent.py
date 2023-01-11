import re;

from mWindowsSDK import DBG_CONTROL_C, STATUS_BREAKPOINT, STATUS_WAKE_SYSTEM_DEBUGGER;

from ..cBugReport import cBugReport;
from ..cErrorDetails import cErrorDetails;
from ..cException import cException;
from ..cProcess import cProcess;
from ..fnGetDebuggerTimeInSeconds import fnGetDebuggerTimeInSeconds;
from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..mCP437 import fsCP437FromBytesString;
from ..mExceptions import cNoAccessToProcessException;

# Return (bEventIsFatal, bEventHasBeenHandled)
HIDE_EVENT_FROM_APPLICATION = (False, True);
REPORT_EVENT_TO_APPLICATION = (False, False);
STOP_DEBUGGING = (True, False);

grbLastEvent = re.compile(
  rb"^"
  rb"Last event: "
  rb"(?:"
    rb"<no event>"  # This means the application send debug output
  rb"|"
    rb"([0-9a-f]+)\.([0-9a-f]+): " # <process-id>.<thread-id>
    rb"(?:"
      rb"(Create|Exit) process [0-9a-f]+\:([0-9a-f]+)(?:, code [0-9a-f]+)?"
    rb"|"
      # After a VERIFIER STOP cdb sometimes reports this event instead of the expected
      # debug breakpoint. The reason for this is unknown.
      rb"(Ignored unload module at [0-9`a-f]+)" 
    rb"|"
      rb"(.*?) \- code ([0-9a-f]+) \(!*\s*(first|second) chance\s*!*\)"
    rb"|"
      rb"Hit breakpoint (\d+)"
    rb")"
  rb")"
  rb"$",
  re.I
);

grbDebuggerTime = re.compile(
  rb"^\s*"
  rb"debugger time: (.*?)"
  rb"\s*$"
);

def cCdbWrapper_ftbHandleLastCdbEvent(oCdbWrapper, asbOutputWhileRunningApplication):
  ### Get information about the last event that caused cdb to pause execution ########################################
  # I have been experiencing a bug where the next command I want to execute (".lastevent") returns nothing. This
  # appears to be caused by an error while executing the command (without an error message) as subsequent commands
  # are not getting executed. As a result, the .printf that outputs the "end marker" is never executed and
  # `fasbReadOutput` detects this as an error in the command and throws an exception. This mostly just affects the
  # next command executed at this point, but I've also seen it affect the second, so I'm going to try and work
  # around it by providing a `bRetryOnTruncatedOutput` argument that informs `fasbExecuteCdbCommand` to
  # detect this truncated output and try the command again for any command that we can safely execute twice.
  asbLastEventOutput = oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b".lastevent;",
    sb0Comment = b"Get information about last event",
    bOutputIsInformative = True,
    bRetryOnTruncatedOutput = True,
  );
  # Sample output:
  # |Last event: 3d8.1348: Create process 3:3d8                
  # |  debugger time: Tue Aug 25 00:06:07.311 2015 (UTC + 2:00)
  # - or -
  # |Last event: c74.10e8: Exit process 4:c74, code 0          
  # |  debugger time: Tue Aug 25 00:06:07.311 2015 (UTC + 2:00)
  asbCleanedLastEventOutput = [sbLine for sbLine in asbLastEventOutput if len(sbLine) != 0]; # Remove empty lines
  assert len(asbCleanedLastEventOutput) == 2, \
      "Invalid .lastevent output:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbLastEventOutput);
  obEventMatch = grbLastEvent.match(asbCleanedLastEventOutput[0]);
  assert obEventMatch, \
      "Invalid .lastevent output on line #1:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbLastEventOutput);
  (
    sb0ProcessIdHex, sb0ThreadIdHex,
    sb0CreateExitProcess, sb0CreateExitProcessIdHex,
    sbIgnoredUnloadModule,
    sb0ExceptionCodeDescription_Unused, sb0ExceptionCode, sbExceptionChance,
    sb0BreakpointId,
  ) = obEventMatch.groups();
  
  ### Parse information about application execution time #############################################################
  obEventTimeMatch = grbDebuggerTime.match(asbCleanedLastEventOutput[1]);
  assert obEventTimeMatch, \
    "Invalid .lastevent output on line #2:\r\n%s" % \
    "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbLastEventOutput);
  oCdbWrapper.oApplicationTimeLock.fAcquire();
  try:
    if oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds:
      # Add the time between when the application was resumed and when the event happened to the total application
      # run time.
      oCdbWrapper.nConfirmedApplicationRunTimeInSeconds += fnGetDebuggerTimeInSeconds(obEventTimeMatch.group(1)) - oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds;
    # Mark the application as suspended by setting nApplicationResumeDebuggerTimeInSeconds to None.
    oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds = None;
    oCdbWrapper.nApplicationResumeTimeInSeconds = None;
  finally:
    oCdbWrapper.oApplicationTimeLock.fRelease();
  
  if sbIgnoredUnloadModule:              # Unload module event: we never requested this; ignore.
    return HIDE_EVENT_FROM_APPLICATION;
  
  ### Parse information about the process and thread or get it if not provided #######################################
  # If the event provides a process and thread id, use those. Otherwise ask cdb about the current process and thread.
  if sb0ProcessIdHex:
    uProcessId = fu0ValueFromCdbHexOutput(sb0ProcessIdHex);
    uThreadId = fu0ValueFromCdbHexOutput(sb0ThreadIdHex);
  else:
    uProcessId = oCdbWrapper.fuGetValueForRegister(b"$tpid", b"Get current process id");
    uThreadId = oCdbWrapper.fuGetValueForRegister(b"$tid", b"Get current thread id");
  
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
  try:
    oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
  except cNoAccessToProcessException:
    if bNewProcess:
      # We cannot access this process, so we should not try to terminate it.
      sMessage = "Unable to access process %d/0x%X because you do not have the required access rights." % (uProcessId, uProcessId);
      assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
          sMessage;
      return STOP_DEBUGGING;
    raise;
  oCdbWrapper.fUpdateCdbISA();
  ### Handle new processes ##########################################################################################
  if bNewProcess:
    if uProcessId == oCdbWrapper.oUtilityProcess.uId:
      oCdbWrapper.fHandleAttachedToUtilityProcess();
    else:
      oCdbWrapper.fHandleAttachedToApplicationProcess();
  
  ### Handle non-exception events ####################################################################################
  if not sb0ProcessIdHex:                # Application debug output events: handle.
    oCdbWrapper.fbFireCallbacks("Application suspended", "Application debug output");
    oCdbWrapper.fHandleDebugOutputFromApplication(asbOutputWhileRunningApplication);
    return HIDE_EVENT_FROM_APPLICATION;
  if sb0BreakpointId is not None:        # Application hit a breakpoint events: handle.
    oCdbWrapper.fbFireCallbacks("Application suspended", "Breakpoint hit");
    oCdbWrapper.fHandleBreakpoint(int(sb0BreakpointId));
    return HIDE_EVENT_FROM_APPLICATION;
  if sb0CreateExitProcess == b"Create":   # Create process events: already handled.
    oCdbWrapper.fbFireCallbacks("Application suspended", "New process created");
    assert sb0CreateExitProcessIdHex == sb0ProcessIdHex, \
      "sb0CreateExitProcessIdHex (%s) is expected to be sb0ProcessIdHex (%s)" % (sb0CreateExitProcessIdHex, sb0ProcessIdHex);
    return HIDE_EVENT_FROM_APPLICATION;
  if sb0CreateExitProcess == b"Exit":     # Exit process events: handle.
    oCdbWrapper.fbFireCallbacks("Application suspended", "Process terminated");
    assert sb0CreateExitProcessIdHex == sb0ProcessIdHex, \
      "sb0CreateExitProcessIdHex (%s) is expected to be sb0ProcessIdHex (%s)" % (sb0CreateExitProcessIdHex, sb0ProcessIdHex);
    assert uProcessId != oCdbWrapper.oUtilityProcess.uId, \
        "The utility process has terminated unexpectedly!";
    oCdbWrapper.fHandleCurrentApplicationProcessTermination();
    return HIDE_EVENT_FROM_APPLICATION;
  
  ### Handle exceptions ##############################################################################################
  uExceptionCode = fu0ValueFromCdbHexOutput(sb0ExceptionCode);
  o0ErrorDetails = cErrorDetails.fo0GetForCode(uExceptionCode);
  sRelatedErrorDefineName = o0ErrorDetails.sDefineName if o0ErrorDetails else "unknown";
  sDetails = "%s chance exception 0x%08X (%s)" % (
    str(sbExceptionChance.capitalize(), "ascii", "strict"),
    uExceptionCode,
    sRelatedErrorDefineName,
  );
  oCdbWrapper.fbFireCallbacks("Application suspended", sDetails);

  # Ignore STATUS_WAKE_SYSTEM_DEBUGGER events
  if uExceptionCode == STATUS_WAKE_SYSTEM_DEBUGGER:  # User pressed CTRL+C event: terminate.
    oCdbWrapper.fbFireCallbacks("Application suspended", "STATUS_WAKE_SYSTEM_DEBUGGER exception thrown.");
    oCdbWrapper.fbFireCallbacks("Log message", "STATUS_WAKE_SYSTEM_DEBUGGER exception thrown.");
    return REPORT_EVENT_TO_APPLICATION;
  # Handle user pressing CTRL+C
  if uExceptionCode == DBG_CONTROL_C:  # User pressed CTRL+C event: terminate.
    oCdbWrapper.fbFireCallbacks("Application suspended", "User pressed CTRL+C");
    oCdbWrapper.fbFireCallbacks("Log message", "User pressed CTRL+C");
    return HIDE_EVENT_FROM_APPLICATION;
  # Handle exceptions in utility process.
  if uProcessId == oCdbWrapper.oUtilityProcess.uId: # Exception in utility process: handle.
    if uExceptionCode != STATUS_BREAKPOINT or not bAttachedToProcess:
      # This is not a breakpoint triggered because we attached to the utility process.
      oCdbWrapper.fHandleExceptionInUtilityProcess(uExceptionCode, sRelatedErrorDefineName);
    return HIDE_EVENT_FROM_APPLICATION;
  
  bApplicationCannotHandleException = sbExceptionChance == b"second";
  oException = cException.foCreateForLastExceptionInProcess(
    oProcess = oCdbWrapper.oCdbCurrentProcess,
    uExpectedCode = uExceptionCode,
    bApplicationCannotHandleException = bApplicationCannotHandleException,
  );
  if uExceptionCode == STATUS_BREAKPOINT and oException.u0Address in oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId.get(uProcessId, []):
    # cdb appears to trigger int3s after the breakpoints have been removed, which we ignore.
    return HIDE_EVENT_FROM_APPLICATION;
  if (
    uExceptionCode == STATUS_BREAKPOINT
    and not bApplicationCannotHandleException
    and oException.o0Module and oException.o0Module.s0BinaryName == "ntdll.dll"
    and oException.o0Function and oException.o0Function.sbSymbol == b"DbgBreakPoint"
  ):
    # I cannot seem to figure out how to stop cdb from triggering a ntdll!DbgUiRemoteBreakin in new processes. From
    # what I understand, using "sxi ibp" should do the trick but it does not appear to have any effect. I'll try to
    # detect these exceptions from the function in which they are triggered; there is a chance of false positives,
    # but I have not seen any. If we detect one, we ignore it:
    return HIDE_EVENT_FROM_APPLICATION;
  
  ### Analyze potential bugs #########################################################################################
  # Free reserve memory before exception analysis
  if oCdbWrapper.o0ReservedMemoryVirtualAllocation:
    oCdbWrapper.o0ReservedMemoryVirtualAllocation.fFree();
    oCdbWrapper.o0ReservedMemoryVirtualAllocation = None;
  o0BugReport = cBugReport.fo0CreateForException(
    oCdbWrapper,
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
  o0BugReport.fReport();
  # If we cannot ignore this bug, stop execution:
  if not oCdbWrapper.oCollateralBugHandler.fbTryToIgnoreException():
    return STOP_DEBUGGING;
  # Collateral bug handler has handled this event; hide it from the application.
  return HIDE_EVENT_FROM_APPLICATION;

