from mWindowsAPI import fds0GetProcessesExecutableName_by_uId;

def cCdbWrapper_fQueueAttachForProcessExecutableNames(oCdbWrapper, *asExecutableNames):
  asExecutableNamesLowered = [s.lower() for s in asExecutableNames];
  for (uProcessId, s0ExecutableName) in fds0GetProcessesExecutableName_by_uId().items():
    # If it is running one of the executables, check if it is being debugged:
    if s0ExecutableName is not None and s0ExecutableName.lower() in asExecutableNamesLowered:
      # If it is not yet being debugged, queue it for attaching:
      if uProcessId not in oCdbWrapper.doProcess_by_uId:
        oCdbWrapper.fQueueAttachForProcessId(uProcessId);
