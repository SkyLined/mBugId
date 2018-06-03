from mWindowsAPI import cConsoleProcess, fsGetProcessISAForId, fStopDebuggingProcessForId;
from .cHelperThread import cHelperThread

def cCdbWrapper_foStartApplicationProcess(oCdbWrapper, sBinaryPath, asArguments):
  oCdbWrapper.fbFireEvent("Log message", "Starting application", {
    "Binary path": sBinaryPath, 
    "Arguments": " ".join([
      " " in sArgument and '"%s"' % sArgument.replace('"', r'\"') or sArgument
      for sArgument in asArguments
    ]),
  });
  oConsoleProcess = cConsoleProcess.foCreateForBinaryPathAndArguments(
    sBinaryPath = sBinaryPath,
    asArguments = asArguments,
    bRedirectStdIn = False,
    bSuspended = True,
  );
  if oConsoleProcess is None:
    sMessage = "Unable to start a new process for binary \"%s\"." % sBinaryPath;
    assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
        sMessage;
    return None;
  # a 32-bit debugger cannot debug 64-bit processes. Report this.
  if oCdbWrapper.sCdbISA == "x86":
    if fsGetProcessISAForId(oConsoleProcess.uId) == "x64":
      assert oConsoleProcess.fbTerminate(5), \
          "Failed to terminate process %d/0x%X within 5 seconds" % \
          (oConsoleProcess.uId, oConsoleProcess.uId);
      sMessage = "Unable to debug a 64-bit process using 32-bit cdb.";
      assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
          sMessage;
      return None;
  oCdbWrapper.fbFireEvent("Log message", "Started process", {
    "Process id": "%d/0x%X" % (oConsoleProcess.uId, oConsoleProcess.uId),
    "Binary name": oConsoleProcess.sBinaryName,
    "Command line": oConsoleProcess.sCommandLine,
  });
  oCdbWrapper.fbFireEvent("Process started", oConsoleProcess);

  # Create helper threads that read the application's output to stdout and stderr. No references to these
  # threads are saved, as they are not needed: these threads only exist to read stdout/stderr output from the
  # application and save it in the report. They will self-terminate when oConsoleProcess.fClose() is called
  # after the process terminates, or this cdb stdio thread dies.
  for (sPipeName, oPipe) in {
    "stdout": oConsoleProcess.oStdOutPipe,
    "stderr": oConsoleProcess.oStdErrPipe,
  }.items():
    sThreadName = "Application %s thread for process %d/0x%X" % (sPipeName, oConsoleProcess.uId, oConsoleProcess.uId);
    oHelperThread = cHelperThread(oCdbWrapper, sThreadName, oCdbWrapper.fApplicationStdOutOrErrHelperThread, oConsoleProcess, oPipe);
    oHelperThread.fStart();
  oCdbWrapper.doConsoleProcess_by_uId[oConsoleProcess.uId] = oConsoleProcess;
  oCdbWrapper.fAttachToProcessForId(oConsoleProcess.uId, bMustBeResumed = True);
  return oConsoleProcess;