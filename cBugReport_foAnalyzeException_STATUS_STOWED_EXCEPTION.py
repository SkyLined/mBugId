import re;
from .cStowedException import cStowedException;
#from cStack import cStack;

def cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION(oBugReport, oProcess, oException):
  # Parameter[0] = paStowedExceptionInformationArray;
  # Parameter[1] = uStowedExceptionInformationArrayLength;
  assert len(oException.auParameters) == 2, \
      "Unexpected number of WinRT language exception parameters (%d vs 2)" % len(oException.auParameters);
  # Get the stowed exceptions and replace information in the bug report:
  aoStowedExceptions = cStowedException.faoCreate(oProcess,
    uauStowedExceptionInformationAddressesAddress = oException.auParameters[0],
    uStowedExceptionInformationAddressesCount = oException.auParameters[1],
  );
  oBugReport.sBugTypeId = "Stowed[%s]" % ",".join([oStowedException.sTypeId for oStowedException in aoStowedExceptions]);
  oBugReport.sBugDescription = ", ".join([oStowedException.sDescription for oStowedException in aoStowedExceptions]);
  oBugReport.sSecurityImpact = ", ".join([oStowedException.sSecurityImpact for oStowedException in aoStowedExceptions if oStowedException.sSecurityImpact]) or None;
#  for oStowedException in aoStowedExceptions:
#    oStack = cStack.foCreateFromAddress(oProcess, oStowedExceptions.pStackTrace, oStowedExceptions.uStackTraceSize);
  return oBugReport;
