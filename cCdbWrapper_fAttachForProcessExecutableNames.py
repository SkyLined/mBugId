import re;

from mWindowsAPI import fdsProcessesExecutableName_by_uId;

def cCdbWrapper_fAttachForProcessExecutableNames(oCdbWrapper, *asExecutableNames):
  asExecutableNamesLowered = [s.lower() for s in asExecutableNames];
  for (uProcessId, sExecutableName) in fdsProcessesExecutableName_by_uId().items():
    # If it is running one of the executables, check if it is being debugged:
    if sExecutableName.lower() in asExecutableNamesLowered:
      # If it is not yet being debugged, queue it for attaching:
      if uProcessId not in oCdbWrapper.doProcess_by_uId:
        oCdbWrapper.fAttachForProcessId(uProcessId);
