from .fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;

def fbUpdateReportForUnallocatedPointer(
  oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress, sViolationVerb, oVirtualAllocation
):
  if not oVirtualAllocation.bFree:
    return False;
  # No memory is allocated in this area
  oBugReport.s0BugTypeId = "AV%s:Unallocated" % sViolationTypeId;
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s unallocated memory at 0x%X." % \
      (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress);
  oBugReport.s0SecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or memory be allocated at the address.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess, oThread, sViolationTypeId)
  );
  return True;
