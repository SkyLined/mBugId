from fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;

def fbUpdateReportForReservedPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  if not oVirtualAllocation.bReserved:
    return False;
  # No memory is allocated in this area, but is is reserved
  oBugReport.sBugTypeId = "AV%s@Reserved" % sViolationTypeId;
  oBugReport.sBugDescription = "Access violation at 0x%X while %s reserved but unallocated memory at 0x%X-0x%X." % \
      (uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation.uStartAddress, \
      oVirtualAllocation.uStartAddress + oVirtualAllocation.uSize);
  oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or " \
      "memory be allocated at the address rather than reserved.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;
