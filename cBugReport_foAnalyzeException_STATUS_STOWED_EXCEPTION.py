import re;
from cStowedException import cStowedException;
from cProcess import cProcess;
from cStack import cStack;

def cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION(oBugReport, oCdbWrapper, oException):
  # Parameter[0] = paStowedExceptionInformationArray;
  # Parameter[1] = uStowedExceptionInformationArrayLength;
  assert len(oException.auParameters) == 2, \
      "Unexpected number of WinRT language exception parameters (%d vs 2)" % len(oException.auParameters);
  pStowedExceptionsAddresses = oException.auParameters[0];
  uStowedExceptionsCount = oException.auParameters[1];
  # Get the stowed exceptions and replace information in the bug report:
  aoStowedExceptions = cStowedException.faoCreate(oCdbWrapper, pStowedExceptionsAddresses, uStowedExceptionsCount);
  oBugReport.sBugTypeId = "[%s]" % ",".join([oStowedException.sTypeId for oStowedException in aoStowedExceptions]);
  oBugReport.sBugDescription = ", ".join([oStowedException.sDescription for oStowedException in aoStowedExceptions]);
  oBugReport.sSecurityImpact = ", ".join([oStowedException.sSecurityImpact for oStowedException in aoStowedExceptions]);
  oBugReport.sProcessBinaryName = oCdbWrapper.oCurrentProcess.sBinaryName;
  oBugReport.oStack = cStack.foCreateFromAddress(oCdbWrapper, aoStowedExceptions[0].pStackTrace, aoStowedExceptions[0].uStackTraceSize);
  return oBugReport;
