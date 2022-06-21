from mWindowsAPI import cVirtualAllocation;

def fbUpdateReportForInvalidPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  uAccessViolationAddress,
  sViolationVerb,
  oVirtualAllocation,
):
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, uAccessViolationAddress);
  # See if the address is valid:
  if not oVirtualAllocation.bInvalid:
    return False;
  oBugReport.s0BugTypeId = "AV%s:Invalid" % sViolationTypeId;
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at invalid address 0x%X." % \
      (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress);
  oBugReport.s0SecurityImpact = "Potentially exploitable security issue, if the address can be controlled.";
  # You normally cannot allocate memory at an invalid address, but the address may be based on controlled data, so we'll
  # try to continue running after this exception just in case.
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    oCollateralBugHandler.fbIgnoreAccessViolationException(
      oCdbWrapper, oProcess, oThread, sViolationTypeId, uAccessViolationAddress,
    )
  );
  return True;
