from ...ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from ...ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress import ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress;
from mWindowsSDK import (
  PAGE_NOACCESS,
  PAGE_READONLY,
  PAGE_READWRITE,
  PAGE_WRITECOPY,
  PAGE_EXECUTE,
  PAGE_EXECUTE_READ,
  PAGE_EXECUTE_READWRITE,
  PAGE_EXECUTE_WRITECOPY,
);

auProtectionThatPreventsWriting = [
  PAGE_NOACCESS,
  PAGE_READONLY,
  PAGE_EXECUTE,
  PAGE_EXECUTE_READ,
];

auProtectionThatPreventsReading = [
  PAGE_NOACCESS,
  PAGE_EXECUTE,
];
auProtectionThatPreventsExecuting = [
  PAGE_NOACCESS,
  PAGE_READONLY,
  PAGE_READWRITE,
  PAGE_WRITECOPY,
];

def fbUpdateReportForAllocatedPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  sViolationVerb,
  uAccessViolationAddress,
  oVirtualAllocation,
):
  if not oVirtualAllocation.bIsAllocated:
    return;
  auProtectionThatPreventsAccess = {
    "R": auProtectionThatPreventsReading,
    "W": auProtectionThatPreventsWriting,
    "E": auProtectionThatPreventsExecuting,
    "?": [], # We lack information about the access type, so we cannot update the report
  }[sViolationTypeId];
  if oVirtualAllocation.uProtection & 0xFF not in auProtectionThatPreventsAccess:
    # It does not appear that this access violation is due to the permission
    # settings on this virtual allocation.
    return;
  (sMemoryProtectionsId, sMemoryProtectionsDescription) = {
    PAGE_NOACCESS:          ("NoAccess",    "allocated but inaccessible"),
    PAGE_READONLY:          ("ReadOnly",    "read-only"),
    PAGE_READWRITE:         ("Read/Write",  "read- and writable"),
    PAGE_WRITECOPY:         ("Read/Write",  "read- and writable"),
    PAGE_EXECUTE:           ("Exec",        "executable"),
    PAGE_EXECUTE_READ:      ("Exec/Read",   "read- and executable"),
    PAGE_EXECUTE_READWRITE: ("Full",        "read-, write-, and executable"),
    PAGE_EXECUTE_WRITECOPY: ("Full",        "read-, write-, and executable"),
  }[oVirtualAllocation.uProtection & 0xFF]; 
  (sBlockSizeId, sBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = \
      ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress(
        uBlockStartAddress = oVirtualAllocation.uStartAddress,
        uBlockSize = oVirtualAllocation.uSize,
        sBlockType = "%s memory" % sMemoryProtectionsDescription,
        uAddress = uAccessViolationAddress,
      );
  if oCdbWrapper.bGenerateReportHTML:
    oBugReport.fAddMemoryRemarks([
      ("Memory allocation start", oVirtualAllocation.uStartAddress, None),
      ("Memory allocation end", oVirtualAllocation.uEndAddress, None)
    ]);
  oBugReport.s0BugTypeId = f"AV{sViolationTypeId}:{sMemoryProtectionsId}{sBlockSizeId}{sBlockOffsetId}";
  oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s %s %s." % \
      (uAccessViolationAddress, sViolationVerb, sBlockOffsetDescription, sBlockSizeDescription);
  oBugReport.s0SecurityImpact = "Unlikely to be an exploitable security issue unless the address can be controlled.";
  # Add a memory dump
  if oCdbWrapper.bGenerateReportHTML:
    # Clamp size, potentially update start if size needs to shrink but end is not changed.
    uMemoryDumpStartAddress, uMemoryDumpSize = ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(
      uAccessViolationAddress, oProcess.uPointerSize, oVirtualAllocation.uStartAddress, oVirtualAllocation.uSize
    );
    oBugReport.fAddMemoryDump(
      uStartAddress = uMemoryDumpStartAddress,
      uEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize,
      asAddressDetailsHTML = ["AV at 0x%X" % uAccessViolationAddress],
    );
  # You normally cannot modify the access rights of memory, so it is impossible for an exploit to avoid this exception.
  # Therefore there is no collateral bug handling. Note that if you can control the address you may be able to point
  # it somewhere that is accessible, e.g. this was some data that got interpreted as a pointer that happened to point
  # to memory that was not accessible, but the data is under attackers control. However, I have decide to assume the
  # exception cannot be avoided.
  return True;
