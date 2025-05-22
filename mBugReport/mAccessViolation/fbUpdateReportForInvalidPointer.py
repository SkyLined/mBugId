def fbUpdateReportForInvalidPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  sViolationVerb,
  uAccessViolationAddress,
  oVirtualAllocation,
):
  # See if the address is valid:
  if not oVirtualAllocation.bInvalid:
    return False;
  oBugReport.s0BugTypeId = "AV%s:Invalid" % sViolationTypeId;
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at invalid address 0x%X." % \
      (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress);
  oBugReport.s0SecurityImpact = "Potentially exploitable security issue, if the address can be controlled.";
  # You normally cannot allocate memory at an invalid address, but it is not
  # normal for a program to use an invalid pointer, so the address may be based
  # on attacker controlled data:
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    oCollateralBugHandler.fbIgnoreAccessViolationException(
      oCdbWrapper, oProcess, oThread, sViolationTypeId, uAccessViolationAddress,
    )
  );
  return True;
