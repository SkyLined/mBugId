import re;
from fauGetAllProcessesIdsForExecutableNames import fauGetAllProcessesIdsForExecutableNames;

def cCdbWrapper_fAttachToProcessesForExecutableNames(oCdbWrapper, *asExecutableNames):
  auProcessIds = fauGetAllProcessesIdsForExecutableNames(*asExecutableNames);
  for uProcessId in auProcessIds:
    # If it is not yet being debugged, do so:
    if uProcessId not in oCdbWrapper.doProcess_by_uId and uProcessId not in oCdbWrapper.auProcessIdsPendingAttach:
      oCdbWrapper.auProcessIdsPendingAttach.append(uProcessId);
