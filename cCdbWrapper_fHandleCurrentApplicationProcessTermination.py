def cCdbWrapper_fHandleCurrentApplicationProcessTermination(oCdbWrapper):
  # A process was terminated. This may be the first time we hear of the process, i.e. the code above may have only
  # just added the process. I do not know why cdb did not throw an event when it was created: maybe it terminated
  # while being created due to some error? Anyway, having added the process in the above code, we'll now mark it as
  # terminated:
  oCdbWrapper.oCdbCurrentProcess.bTerminated = True;
  oCdbWrapper.fbFireCallbacks("Process terminated", oCdbWrapper.oCdbCurrentProcess);
  oCdbWrapper.fbFireCallbacks("Log message", "Terminated application process", {
    "Process id": oCdbWrapper.oCdbCurrentProcess.uId,
    "Is main process": (oCdbWrapper.oCdbCurrentProcess.uId in oCdbWrapper.auMainProcessIds) and "yes" or "no",
  });
