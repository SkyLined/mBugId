from ...ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress import ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress;

def fbUpdateReportForGuardPagePointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  sViolationVerb,
  uAccessViolationAddress,
  oVirtualAllocation,
):
  if not oVirtualAllocation.bGuard:
    return False;
  # No memory is allocated in this area, but is is reserved
  (sBlockSizeId, sBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = \
      ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress(
        uBlockStartAddress = oVirtualAllocation.uStartAddress,
        uBlockSize = oVirtualAllocation.uSize,
        sBlockType = "guard page",
        uAddress = uAccessViolationAddress,
      );
  oBugReport.s0BugTypeId = "AV%s:Guard%s%s" % (sViolationTypeId, sBlockSizeId, sBlockOffsetId);
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while %s a guard page at 0x%X-0x%X." % \
      (uAccessViolationAddress, sViolationVerb, oVirtualAllocation.uStartAddress, \
      oVirtualAllocation.uStartAddress + oVirtualAllocation.uSize);
  oBugReport.s0SecurityImpact = "Unlikely to be an exploitable security issue; guard pages are allocated to trigger " \
      "this type of access violation, so this appears to be a by-design error handling.";
  # Guard Pages are created to detect when an application is accessing memory
  # out-of-bounds, so it seems this access violation cannot be avoided. We will
  # not set up a collateral bug handler to try to see what happens if we can
  # avoid the AV.
  return True;
