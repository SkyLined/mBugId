from ..ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from ..ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress import ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress;
from mWindowsAPI import cVirtualAllocation;
from mWindowsSDK import *;

def fbUpdateReportForAllocatedPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  uAccessViolationAddress,
  sViolationVerb,
):
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, uAccessViolationAddress);
  if not oVirtualAllocation.bAllocated:
    return False;
  # Memory is allocated in this area, but apparantly not accessible in the way the code tried to.
  if oCdbWrapper.bGenerateReportHTML:
    oBugReport.atxMemoryRemarks.append(("Memory allocation start", oVirtualAllocation.uStartAddress, None));
    oBugReport.atxMemoryRemarks.append(("Memory allocation end", oVirtualAllocation.uEndAddress, None));
  if oVirtualAllocation.bGuard:
    (sMemoryProtectionsId, sMemoryProtectionsDescription) = ("Guard", "guard page");
  else:
    (sMemoryProtectionsId, sMemoryProtectionsDescription) = {
      PAGE_NOACCESS:          ("NoAccess",    "allocated but inaccessible"),
      PAGE_READONLY:          ("ReadOnly",    "read-only"),
      PAGE_READWRITE:         ("Read/Write",  "read- and writable"),
      PAGE_WRITECOPY:         ("Read/Write",  "read- and writable"),
      PAGE_EXECUTE:           ("Exec",        "executable"),
      PAGE_EXECUTE_READ:      ("Exec/Read",   "read- and executable"),
      PAGE_EXECUTE_READWRITE: ("Full",        "read-, write-, and execute"),
      PAGE_EXECUTE_WRITECOPY: ("Full",        "read-, write-, and execute"),
    }[oVirtualAllocation.uProtection & 0xFF]; 
  (sBlockSizeId, sBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = \
      ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress(
        uBlockStartAddress = oVirtualAllocation.uStartAddress,
        uBlockSize = oVirtualAllocation.uSize,
        sBlockType = "%s memory" % sMemoryProtectionsDescription,
        uAddress = uAccessViolationAddress,
      );
  if sViolationTypeId == "W":
    assert not oVirtualAllocation.bWritable or oVirtualAllocation.bGuard, \
        "A write access violation in writable memory should not be possible";
  elif sViolationTypeId == "R":
    assert not oVirtualAllocation.bReadable or oVirtualAllocation.bGuard, \
        "A read access violation in readble memory should not be possible";
  elif sViolationTypeId == "E":
    assert not oVirtualAllocation.bExecutable or oVirtualAllocation.bGuard, \
        "A read access violation in readble memory should not be possible";
  oBugReport.s0BugTypeId = "AV%s:%s%s%s" % (sViolationTypeId, sMemoryProtectionsId, sBlockSizeId, sBlockOffsetId);
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
      uMemoryDumpStartAddress,
      uMemoryDumpStartAddress + uMemoryDumpSize,
      "Memory near access violation at 0x%X" % uAccessViolationAddress,
    );
  # You normally cannot modify the access rights of memory, so it is impossible for an exploit to avoid this exception.
  # Therefore there is no collateral bug handling. Note that if you can control the address you may be able to point
  # it somewhere that is accessible, e.g. this was some data that got interpreted as a pointer that happened to point
  # to memory that was not accessible, but the data is under attackers control. However, I have decide to assume the
  # exception cannot be avoided.
  return True;
