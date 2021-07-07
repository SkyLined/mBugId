from mWindowsSDK import ERROR_INVALID_NAME, fsGetWin32ErrorCodeDescription;
from mWindowsAPI import cConsoleProcess, fsGetISAForProcessId;

from .cHelperThread import cHelperThread;

__gauProcessesThatShouldBeResumedAfterAttaching = [];
def __gfResumeProcessAfterAttach(oCdbWrapper, oAttachedToProcess):
  if oAttachedToProcess.uId in __gauProcessesThatShouldBeResumedAfterAttaching:
    __gauProcessesThatShouldBeResumedAfterAttaching.remove(oAttachedToProcess.uId);
    oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = b"~*m",
      sb0Comment = b"Resume threads for process 0x%X" % (oAttachedToProcess.uId),
    ); # TODO: check output
    if len(__gauProcessesThatShouldBeResumedAfterAttaching) == 0:
      # There are no processes that need to be resumed: we no longer need to
      # handle this event.
      oCdbWrapper.fbRemoveCallback("Process attached", __gfResumeProcessAfterAttach);

def cCdbWrapper_foStartApplicationProcess(oCdbWrapper, sBinaryPath, asArguments):
  oCdbWrapper.fbFireCallbacks("Log message", "Starting application", {
    "Binary path": sBinaryPath, 
    "Arguments": " ".join([
      " " in sArgument and '"%s"' % sArgument.replace('"', r'\"') or sArgument
      for sArgument in asArguments
    ]),
  });
  try:
    oConsoleProcess = cConsoleProcess.foCreateForBinaryPathAndArguments(
      sBinaryPath = sBinaryPath,
      asArguments = asArguments,
      bRedirectStdIn = False,
      bSuspended = True,
    );
  except WindowsError as oWindowsError:
    sErrorDescription = fsGetWin32ErrorCodeDescription(oWindowsError.errno);
    sMessage = "Unable to start a new process for binary path \"%s\": %s." % \
        (sBinaryPath, sErrorDescription);
    assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
        sMessage;
    return None;
  oCdbWrapper.aoApplicationProcesses.append(oConsoleProcess);
  # a 32-bit debugger cannot debug 64-bit processes. Report this.
  if oCdbWrapper.sCdbISA == "x86":
    if fsGetISAForProcessId(oConsoleProcess.uId) == "x64":
      assert oConsoleProcess.fbTerminate(5), \
          "Failed to terminate process %d/0x%X within 5 seconds" % \
          (oConsoleProcess.uId, oConsoleProcess.uId);
      sMessage = "Unable to debug a 64-bit process using 32-bit cdb.";
      assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
          sMessage;
      return None;
  oCdbWrapper.fbFireCallbacks("Log message", "Started process", {
    "Process id": "%d/0x%X" % (oConsoleProcess.uId, oConsoleProcess.uId),
    "Binary name": oConsoleProcess.sBinaryName,
    "Command line": oConsoleProcess.sCommandLine,
  });
  oCdbWrapper.fbFireCallbacks("Process started", oConsoleProcess);
  
  # Create helper threads that read the application's output to stdout and stderr. No references to these
  # threads are saved, as they are not needed: these threads only exist to read stdout/stderr output from the
  # application and save it in the report. They will self-terminate when oConsoleProcess.fClose() is called
  # after the process terminates, or this cdb stdio thread dies.
  for (sPipeName, oPipe) in {
    "stdout": oConsoleProcess.oStdOutPipe,
    "stderr": oConsoleProcess.oStdErrPipe,
  }.items():
    oCdbWrapper.aoApplicationStdOutAndStdErrPipes.append(oPipe);
    sThreadName = "Application %s thread for process %d/0x%X" % (sPipeName, oConsoleProcess.uId, oConsoleProcess.uId);
    oHelperThread = cHelperThread(oCdbWrapper, sThreadName, oCdbWrapper.fApplicationStdOutOrErrHelperThread, oConsoleProcess, oPipe, sPipeName);
    oHelperThread.fStart();
  
  # We need cdb to attach to the process and we need to resume the process once
  # it has attached. We'll create an event handler that detects when cdb has
  # attached to a process to resume the process and then queue an "attach to
  # process".
  if len(__gauProcessesThatShouldBeResumedAfterAttaching) == 0:
    oCdbWrapper.fAddCallback("Process attached", __gfResumeProcessAfterAttach);
  __gauProcessesThatShouldBeResumedAfterAttaching.append(oConsoleProcess.uId);
  
  oCdbWrapper.fQueueAttachForProcessId(oConsoleProcess.uId);
  
  return oConsoleProcess;