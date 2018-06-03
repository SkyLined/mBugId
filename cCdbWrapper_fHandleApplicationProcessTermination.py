def cCdbWrapper_fHandleApplicationProcessTermination(oCdbWrapper, uProcessId):
  oProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
  # A process was terminated. This may be the first time we hear of the process, i.e. the code above may have only
  # just added the process. I do not know why cdb did not throw an event when it was created: maybe it terminated
  # while being created due to some error? Anyway, having added the process in the above code, we'll now mark it as
  # terminated:
  oProcess.bTerminated = True;
  oCdbWrapper.fbFireEvent("Process terminated", oProcess);
  oCdbWrapper.fbFireEvent("Log message", "Terminated application process", {
    "Process id": uProcessId,
    "Is main process": (oProcess.uId in oCdbWrapper.auMainProcessIds) and "yes" or "no",
  });
  # If we have console stdin/stdout/stderr pipes, close them:
  oConsoleProcess = oCdbWrapper.doConsoleProcess_by_uId.get(uProcessId);
  if oConsoleProcess:
    del oCdbWrapper.doConsoleProcess_by_uId[uProcessId];
