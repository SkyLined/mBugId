from .fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;
from ..fsGetNumberDescription import fsGetNumberDescription;

def fbUpdateReportForCollateralPoisonPointer(
  oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress, sViolationVerb, oVirtualAllocation
):
  iOffset = oCdbWrapper.oCollateralBugHandler.fiGetOffsetForPoisonedAddress(oProcess, uAccessViolationAddress);
  if iOffset is None:
    # This is not near the poisoned address used by collateral
    return False;
  sSign = iOffset < 0 and "-" or "+";
  sOffset = "%s%s" % (sSign, fsGetNumberDescription(abs(iOffset), sSign));
  oBugReport.sBugTypeId = "AV%s:Poison%s" % (sViolationTypeId, sOffset);
  oBugReport.sBugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X using a poisoned value provided by cBugId." % \
    (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress);
  oBugReport.sSecurityImpact = "Highly likely to be an exploitable security issue if your exploit can poison this value.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess, oThread, sViolationTypeId)
  );
  return True;

