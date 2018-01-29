from fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;
from ..fsGetNumberDescription import fsGetNumberDescription;

def fbUpdateReportForCollateralPoisonPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  iOffset = oCdbWrapper.oCollateralBugHandler.fiGetOffsetForPoisonedAddress(oProcess, uAccessViolationAddress);
  if iOffset is None:
    # This is not near the poisoned address used by collateral
    return False;
  sSign = iOffset < 0 and "-" or "+";
  sOffset = "%s%s" % (sSign, fsGetNumberDescription(abs(iOffset), sSign));
  oBugReport.sBugTypeId = "AV%s@Poison%s" % (sViolationTypeId, sOffset);
  oBugReport.sBugDescription = "Access violation while %s memory at 0x%X using a poisoned value provided by cBugId." % \
    (sViolationTypeDescription, uAccessViolationAddress);
  oBugReport.sSecurityImpact = "Highly likely to be an exploitable security issue if your exploit can poison this value.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;

