from ...fsGetNumberDescription import fsGetNumberDescription;

def fbUpdateReportForCollateralPoisonPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  sViolationVerb,
  uAccessViolationAddress,
):
  i0Offset = oCdbWrapper.oCollateralBugHandler.fi0GetOffsetForPoisonedAddress(oProcess, uAccessViolationAddress);
  if i0Offset is None:
    # This is not near the poisoned address used by collateral
    return False;
  iOffset = i0Offset;
  sSign = iOffset < 0 and "-" or "+";
  sOffset = "%s%s" % (sSign, fsGetNumberDescription(abs(iOffset), sSign));
  oBugReport.s0BugTypeId = "AV%s:Poison%s" % (sViolationTypeId, sOffset);
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X using a poisoned value provided by cBugId." % \
    (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress);
  oBugReport.s0SecurityImpact = "Highly likely to be an exploitable security issue if your exploit can poison this value.";
  # This address most likely came from a previous access violation we ignored
  # through collateral bug handling, so it makes sense to assume an attacker
  # could control the value of the address and avoid this AV too:
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    oCollateralBugHandler.fbIgnoreAccessViolationException(
      oCdbWrapper, oProcess, oThread, sViolationTypeId, uAccessViolationAddress,
    )
  );
  return True;

