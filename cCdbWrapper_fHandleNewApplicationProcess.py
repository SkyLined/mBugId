from cProcess import cProcess;

def cCdbWrapper_fHandleNewApplicationProcess(oCdbWrapper, uProcessId, bIsMainProcess):
  # A new process was started and it loaded NTDLL, which is one of the first things that happens.
  assert uProcessId not in oCdbWrapper.doProcess_by_uId, \
      "The process %d/0x%X is reported to have started twice!" % (uProcessId, uProcessId);
  # Create a new process object and make it the current process.
  oProcess = oCdbWrapper.oCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId] = cProcess(oCdbWrapper, uProcessId);
  # If we're attaching to processes, make sure this is the one we expected to attach to.
  bAttachedToProcess = oCdbWrapper.auProcessIdsPendingAttach;
  if bAttachedToProcess:
    uPendingAttachProcessId = oCdbWrapper.auProcessIdsPendingAttach.pop(0);
    assert uPendingAttachProcessId == uProcessId, \
        "Expected to attach to process %d, got %d" % (uPendingAttachProcessId, uProcessId);
  # If this is a main process, add it to the list.
  if bIsMainProcess:
    oCdbWrapper.aoMainProcesses.append(oProcess);
  sEventDescription = bAttachedToProcess and "Attached to process" or "Started process";
  # If we are attaching to processes, the current process should be the last one we tried to attach to:
  oCdbWrapper.fbFireEvent("Log message", sEventDescription, {
    "Is main process": bIsMainProcess and "yes" or "no",
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
    "Binary name": oProcess.sBinaryName,
    "Command line": oProcess.sCommandLine,
  });
  oCdbWrapper.fbFireEvent(sEventDescription, oProcess);
  # If we have a JobObject, add this process to it.
  if oCdbWrapper.oJobObject and not oCdbWrapper.oJobObject.fbAddProcessForId(uProcessId):
    if not oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired:
      # The limits no longer affect the application after the first time this happens, so it is only reported once.
      oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired = True;
      oCdbWrapper.fbFireEvent("Failed to apply application memory limits", oProcess);
    oCdbWrapper.fbFireEvent("Failed to apply process memory limits", oProcess);
  # Make sure child processes of the new process are debugged as well.
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".childdbg 1;",
    sComment = "Debug child processes",
    bRetryOnTruncatedOutput = True,
  );
