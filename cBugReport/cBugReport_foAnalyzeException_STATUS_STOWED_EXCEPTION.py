from ..cStowedException import cStowedException;

def cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION(oBugReport, oProcess, oWindowsAPIThread, oException):
  # Parameter[0] = paStowedExceptionInformationArray;
  # Parameter[1] = uStowedExceptionInformationArrayLength;
  assert len(oException.auParameters) == 2, \
      "Unexpected number of WinRT language exception parameters (%d vs 2)" % len(oException.auParameters);
  # Get the stowed exceptions and replace information in the bug report:
  aoStowedExceptions = cStowedException.faoCreateForListAddressAndCount(oProcess,
    oException.auParameters[0],
    oException.auParameters[1],
  );
  oBugReport.s0BugTypeId = "Stowed[%s]" % ",".join([oStowedException.sTypeId for oStowedException in aoStowedExceptions]);
  oBugReport.s0BugDescription = ", ".join([oStowedException.sDescription for oStowedException in aoStowedExceptions]);
  oBugReport.s0SecurityImpact = ", ".join([
    oStowedException.s0SecurityImpact
    for oStowedException in aoStowedExceptions
    if oStowedException.s0SecurityImpact
  ]) or None;
#  for oStowedException in aoStowedExceptions:
#    oStack = cStack.foCreateFromAddress(oProcess, oStowedExceptions.pStackTrace, oStowedExceptions.uStackTraceSize);
  return oBugReport;
