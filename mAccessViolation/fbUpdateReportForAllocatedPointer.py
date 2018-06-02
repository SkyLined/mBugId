from ..ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from ..ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress import ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress;

def fbUpdateReportForAllocatedPointer(
  oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  if not oVirtualAllocation.bAllocated:
    return False;
  # Memory is allocated in this area, but apparantly not accessible in the way the code tried to.
  if oCdbWrapper.bGenerateReportHTML:
    oBugReport.atxMemoryRemarks.append(("Memory allocation start", oVirtualAllocation.uStartAddress, None));
    oBugReport.atxMemoryRemarks.append(("Memory allocation end", oVirtualAllocation.uEndAddress, None));
  sMemoryProtectionsDescription = {
    0x01: "allocated but inaccessible", 0x02: "read-only",            0x04: "read- and writable",  0x08: "read- and writable",
    0x10: "executable",                 0x20: "read- and executable",
  }[oVirtualAllocation.uProtection];
  (sBlockSizeId, sBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = \
      ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress(
        uBlockStartAddress = oVirtualAllocation.uStartAddress,
        uBlockSize = oVirtualAllocation.uSize,
        sBlockType = "%s memory" % sMemoryProtectionsDescription,
        uAddress = uAccessViolationAddress,
      );
  sBlockSizeAndOffsetId = sBlockSizeId + sBlockOffsetId;
  sBlockOffsetAndSizeDescription = sBlockOffsetDescription + " " + sBlockSizeDescription;
  if sViolationTypeId == "W":
    assert not oVirtualAllocation.bWritable, \
        "A write access violation in writable memory should not be possible";
    oBugReport.sBugTypeId = "W2RO%s" % sBlockSizeAndOffsetId;
    oBugReport.sBugDescription = "Access violation while writing to read-only memory %s." % sBlockOffsetAndSizeDescription;
  elif sViolationTypeId == "R":
    assert not oVirtualAllocation.bReadable, \
        "A read access violation in readble memory should not be possible";
    oBugReport.sBugTypeId = "AVR%s" % sBlockSizeAndOffsetId;
    oBugReport.sBugDescription = "Access violation while reading from inaccessible memory %s." % sBlockOffsetAndSizeDescription;
  elif sViolationTypeId == "E":
    oBugReport.sBugTypeId = "DEP%s" % sBlockSizeAndOffsetId;
    oBugReport.sBugDescription = "Data execution prevention triggered an access violation while attempting to " + \
        "execute non-executable memory %s." % sBlockOffsetAndSizeDescription;
  else:
    oBugReport.sBugTypeId = "AV%s%s" % (sViolationTypeId, sBlockSizeAndOffsetId);
    oBugReport.sBugDescription = "An Access Violation exception happend while attempting to %s memory %s" % \
        (sViolationTypeDescription, sBlockOffsetAndSizeDescription);
  oBugReport.sSecurityImpact = "Unlikely to be an exploitable security issue unless the address can be controlled.";
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
