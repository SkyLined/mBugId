from .cProcess import cProcess;

def cCdbWrapper_fHandleNewApplicationProcess(oCdbWrapper, uProcessId):
  # This first application process we attach to for an UWP application is the main process.
  if oCdbWrapper.oUWPApplication and not oCdbWrapper.bUWPApplicationStarted:
    oCdbWrapper.bUWPApplicationStarted = True;
    oCdbWrapper.auMainProcessIds.append(uProcessId);
  bIsMainProcess = uProcessId in oCdbWrapper.auMainProcessIds;
  
  # A new process was started and it loaded NTDLL, which is one of the first things that happens.
  assert uProcessId not in oCdbWrapper.doProcess_by_uId, \
      "The process %d/0x%X is reported to have started twice!" % (uProcessId, uProcessId);
  # Find out if we attached to this process, or if a sub-process was started.
  if uProcessId in oCdbWrapper.auProcessIdsPendingAttach:
    oCdbWrapper.auProcessIdsPendingAttach.remove(uProcessId);
  # Create a new process object and make it the current process.
  oProcess = oCdbWrapper.doProcess_by_uId[uProcessId] = cProcess(oCdbWrapper, uProcessId);
  oCdbWrapper.fSelectProcess(uProcessId);
  
  # If we have a JobObject, add this process to it.
  if oCdbWrapper.oJobObject and not oCdbWrapper.oJobObject.fbAddProcessForId(uProcessId):
    if not oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired:
      # The limits no longer affect the application after the first time this happens, so it is only reported once.
      oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired = True;
      oCdbWrapper.fbFireEvent("Failed to apply application memory limits", oProcess);
    oCdbWrapper.fbFireEvent("Failed to apply process memory limits", oProcess);
  
  # Fire events
  oCdbWrapper.fbFireEvent("Log message", "Process attached", {
    "Is main process": bIsMainProcess and "yes" or "no",
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
    "Binary name": oProcess.sBinaryName,
    "Command line": oProcess.sCommandLine,
  });
  oCdbWrapper.fbFireEvent("Process attached", oProcess);
  
  # Make sure child processes of the new process are debugged as well.
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".childdbg 1;",
    sComment = "Debug child processes",
    bRetryOnTruncatedOutput = True,
  ); # TODO: check output
  
  # Make sure threads are resumed if the process is suspended
  if uProcessId in oCdbWrapper.auProcessIdsThatNeedToBeResumedAfterAttaching:
    oCdbWrapper.auProcessIdsThatNeedToBeResumedAfterAttaching.remove(uProcessId);
    oCdbWrapper.fasExecuteCdbCommand(
      sCommand = "~*m",
      sComment = "Resume threads for process %d/0x%X" % (uProcessId, uProcessId),
    ); # TODO: check output
  
  # As soon as we have attached to the first application process and resumed it, the application is considered to have
  # been started.
  if not oCdbWrapper.bApplicationStarted:
    oCdbWrapper.fbFireEvent("Application running");
    oCdbWrapper.bApplicationStarted = True;