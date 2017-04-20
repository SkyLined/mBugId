import re;
from cProcess import cProcess;
from dxConfig import dxConfig;

def fDebugOutputProcesses(oCdbWrapper, sMessage):
  asDebugOutput = oCdbWrapper.fasSendCommandAndReadOutput(
    '.printf "%s\\r\\n";' % sMessage,
    bShowOnlyCommandOutput = True,
  );
  if not oCdbWrapper.bCdbRunning: return;
  assert len(asDebugOutput) == 1, "Unexpected output: %s" % repr(asDebugOutput);
  if dxConfig["bOutputProcesses"]:
    print "@@@ %s" % asDebugOutput[0];

def cCdbWrapper_foSetCurrentProcessAfterApplicationRan(oCdbWrapper, uProcessId, sCreateOrExit):
  if uProcessId not in oCdbWrapper.doProcess_by_uId:
    # A new process was created or attached to
    assert uProcessId not in oCdbWrapper.doProcess_by_uId, \
        "Process %d/0x%X cannot be created twice!" % (uProcessId, uProcessId);
    oProcess = cProcess.foCreateForCurrentProcess(oCdbWrapper);
    assert oProcess.uId == uProcessId, \
        "Expected the current process to be %d/0x%X but got %d/0x%X" % (uProcessId, uProcessId, oProcess.uId, oProcess.uId);
    bIsFirstProcess = len(oCdbWrapper.doProcess_by_uId) == 0;
    oCdbWrapper.doProcess_by_uId[uProcessId] = oProcess;
    # If cdb has created this process (i.e. it is not attaching to any process ids), the first process is the "main"
    # process.
    if bIsFirstProcess and len(oCdbWrapper.auProcessIdsPendingAttach) == 0:
      assert len(oCdbWrapper.auMainProcessIds) == 0, "Only one main process can exist.";
      # Note: when attaching to processes, this list is created earlier as a copy of auProcessIdsPendingAttach.
      oCdbWrapper.auMainProcessIds = [uProcessId];
    # If the debugger attached to this process, remove it from the list of pending attaches:
    if len(oCdbWrapper.auProcessIdsPendingAttach) > 0:
      uPendingAttachProcessId = oCdbWrapper.auProcessIdsPendingAttach.pop(0);
      assert uPendingAttachProcessId == uProcessId, \
          "Expected to attach to process %d, got %d" % (uPendingAttachProcessId, uProcessId);
      fDebugOutputProcesses(oCdbWrapper, "* Attached to process %d/0x%X (%s)." % (uProcessId, uProcessId, oProcess.sBinaryName));
      bInitialProcessesCreated = len(oCdbWrapper.auProcessIdsPendingAttach) == 0;
    else:
      fDebugOutputProcesses(oCdbWrapper, "* New process %d/0x%X (%s)." % (uProcessId, uProcessId, oProcess.sBinaryName));
      # Make sure all child processes of this process are debugged as well.
    # This may be superfluous, as I believe this is a global flag, not per-process, but it should have negligable
    # affect on performance and would prevent bugs if this assumption is not true.
    oCdbWrapper.fasSendCommandAndReadOutput(".childdbg 1; $$ Debug child processes");
    if not oCdbWrapper.bCdbRunning: return;
    if dxConfig["bEnsurePageHeap"]:
      oCdbWrapper.fEnsurePageHeapIsEnabledInCurrentProcess();
      if not oCdbWrapper.bCdbRunning: return;
  else:
    oProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
  oCdbWrapper.oCurrentProcess = oProcess;
  if sCreateOrExit == "Exit":
    # A process was terminated. This may be the first time we hear of the process, i.e. the code above may have only
    # just added the process. I do not know why cdb did not throw an event when it was created: maybe it terminated
    # while being created due to some error? Anyway, having added the process in the above code, we'll now mark it as
    # terminated:
    assert uProcessId not in oCdbWrapper.auProcessIdsPendingDelete, \
        "Process %d/0x%X cannot be terminated twice!" % (uProcessId, uProcessId);
    oProcess.bTerminated = True;
    oCdbWrapper.auProcessIdsPendingDelete.append(uProcessId);
    fDebugOutputProcesses(oCdbWrapper, "* Terminated process %d/0x%X (%s)." % (uProcessId, uProcessId, oProcess.sBinaryName));
    oCdbWrapper.bApplicationTerminated = len(oCdbWrapper.auProcessIdsPendingDelete) == len(oCdbWrapper.doProcess_by_uId);
    if uProcessId in oCdbWrapper.auMainProcessIds:
      oCdbWrapper.fMainProcessTerminatedCallback(uProcessId, oProcess.sBinaryName);
  return oProcess;
