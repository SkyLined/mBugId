from ..ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress import ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress;

def fbUpdateReportForReservedPointer(
  oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress, sViolationVerb, oVirtualAllocation
):
  if not oVirtualAllocation.bReserved:
    return False;
  # No memory is allocated in this area, but is is reserved
  (sBlockSizeId, sBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = \
      ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress(
        uBlockStartAddress = oVirtualAllocation.uStartAddress,
        uBlockSize = oVirtualAllocation.uSize,
        sBlockType = "reserved memory",
        uAddress = uAccessViolationAddress,
      );
  oBugReport.s0BugTypeId = "AV%s:Reserved%s%s" % (sViolationTypeId, sBlockSizeId, sBlockOffsetId);
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while %s reserved but unallocated memory at 0x%X-0x%X." % \
      (uAccessViolationAddress, sViolationVerb, oVirtualAllocation.uStartAddress, \
      oVirtualAllocation.uStartAddress + oVirtualAllocation.uSize);
  oBugReport.s0SecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or " \
      "memory be allocated at the address rather than reserved.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    oCollateralBugHandler.fbIgnoreAccessViolationException(
      oCdbWrapper, oProcess, oThread, sViolationTypeId, uAccessViolationAddress,
    )
  );
  return True;
