def fbUpdateReportForUnallocatedPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  sViolationVerb,
  uAccessViolationAddress,
  oVirtualAllocation,
):
  if not oVirtualAllocation.bFree:
    return False;
  # No memory is allocated in this area
  oBugReport.s0BugTypeId = "AV%s:Unallocated" % sViolationTypeId;
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s unallocated memory at 0x%X." % \
      (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress);
  oBugReport.s0SecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or memory be allocated at the address.";
  # Attacker might be able to have the access point to allocated memory, so we
  # can try to ignore the exception and see what happens next:
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    oCollateralBugHandler.fbIgnoreAccessViolationException(
      oCdbWrapper, oProcess, oThread, sViolationTypeId, uAccessViolationAddress,
    )
  );
  return True;
