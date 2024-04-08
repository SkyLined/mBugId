from ..dxConfig import dxConfig;

def cCdbWrapper_fHandleAttachedToApplicationProcess(oCdbWrapper):
  if dxConfig["bEnsurePageHeap"]:
    oCdbWrapper.oCdbCurrentProcess.fEnsurePageHeapIsEnabled();
  # This first application process we attach to for an UWP application is the main process.
  if oCdbWrapper.o0UWPApplication and not oCdbWrapper.bUWPApplicationStarted:
    oCdbWrapper.bUWPApplicationStarted = True;
    oCdbWrapper.auMainProcessIds.append(oCdbWrapper.oCdbCurrentProcess.uId);
    bIsMainProcess = True;
  else:
    bIsMainProcess = oCdbWrapper.oCdbCurrentProcess.uId in oCdbWrapper.auMainProcessIds;
  
  if oCdbWrapper.sCdbISA != oCdbWrapper.oCdbCurrentProcess.sISA:
    # We assume that the user can specify the ISA of the target application when they start cBugId, so if a main
    # process is mismatched, this could have been prevented.
    bPreventable = bIsMainProcess;
    if not oCdbWrapper.oCdbCurrentProcess.oCdbWrapper.fbFireCallbacks("Cdb ISA not ideal", oCdbWrapper.oCdbCurrentProcess, oCdbWrapper.sCdbISA, bPreventable):
      # This is fatal if it's preventable and there is no callback handler
      assert not bPreventable, \
          "Cdb ISA %s is not ideal for debugging %s process 0x%X (running %s)." % \
          (oCdbWrapper.sCdbISA, oCdbWrapper.oCdbCurrentProcess.sISA, oCdbWrapper.oCdbCurrentProcess.uId, oCdbWrapper.oCdbCurrentProcess.sBinaryName);
  
  # If we have a JobObject, add this process to it.
  if oCdbWrapper.oJobObject and not oCdbWrapper.oJobObject.fbAddProcessForId(oCdbWrapper.oCdbCurrentProcess.uId):
    if not oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired:
      # The limits no longer affect the application after the first time this happens, so it is only reported once.
      oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired = True;
      oCdbWrapper.fbFireCallbacks("Failed to apply application memory limits", oCdbWrapper.oCdbCurrentProcess);
    oCdbWrapper.fbFireCallbacks("Failed to apply process memory limits", oCdbWrapper.oCdbCurrentProcess);
  
  # Fire events
  oCdbWrapper.fbFireCallbacks("Log message", "Process attached", {
    "Is main process": bIsMainProcess and "yes" or "no",
    "Process Id": "0x%X" % (oCdbWrapper.oCdbCurrentProcess.uId,),
    "Binary name": oCdbWrapper.oCdbCurrentProcess.sBinaryName,
    "Command line":oCdbWrapper.oCdbCurrentProcess.sCommandLine,
  });
  oCdbWrapper.fbFireCallbacks("Process attached", oCdbWrapper.oCdbCurrentProcess);
  
  # Make sure child processes of the new process are debugged as well.
  oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b".childdbg 1;",
    sb0Comment = b"Debug child processes",
    bRetryOnTruncatedOutput = True,
  ); # TODO: check output
