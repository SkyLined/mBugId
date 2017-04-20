from fsGetNumberDescription import fsGetNumberDescription;
from ftsGetHeapBlockAndOffsetIdAndDescription import ftsGetHeapBlockAndOffsetIdAndDescription;
from ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;

def fSetBugReportPropertiesForAccessViolationUsingPageHeapAllocation(
  oBugReport,
  uAccessViolationAddress, sViolationTypeId, sViolationTypeDescription,
  oPageHeapAllocation,
  uPointerSize, bGenerateReportHTML,
):
  if oPageHeapAllocation.uBlockStartAddress and oPageHeapAllocation.uBlockSize:
    if bGenerateReportHTML:
      uMemoryDumpStartAddress = oPageHeapAllocation.uBlockStartAddress;
      uMemoryDumpSize = oPageHeapAllocation.uBlockSize;
    if bGenerateReportHTML:
      if uAccessViolationAddress < oPageHeapAllocation.uBlockStartAddress:
        uPrefix = oPageHeapAllocation.uBlockStartAddress - uAccessViolationAddress;
        uMemoryDumpStartAddress -= uPrefix;
        uMemoryDumpSize += uPrefix;
      elif uAccessViolationAddress >= oPageHeapAllocation.uBlockEndAddress:
        uPostFix = uAccessViolationAddress - oPageHeapAllocation.uBlockEndAddress + 1;
        uMemoryDumpSize += uPostFix;
      # Check if we're not trying to dump a rediculous amount of memory:
      # Clamp start and end address
      uMemoryDumpStartAddress, uMemoryDumpSize = ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(
        uAccessViolationAddress, uPointerSize, uMemoryDumpStartAddress, uMemoryDumpSize
      );
      oBugReport.fAddMemoryDump(
        uMemoryDumpStartAddress,
        uMemoryDumpStartAddress + uMemoryDumpSize,
        "Memory near access violation at 0x%X" % uAccessViolationAddress,
      );
    bOutOfBounds = (uAccessViolationAddress < oPageHeapAllocation.uBlockStartAddress) \
                or (uAccessViolationAddress >= oPageHeapAllocation.uBlockEndAddress);
  else:
    assert oPageHeapAllocation.bFreed, \
        "If the page was not freed, we should be able to find the start and size of the heap block!!";
    # If the access was outside of the allocation, it was out of bounds, otherwise we can't be sure since we do not
    # know where the block was inside the allocation. Let's assume it was ok and only report UAF in such cases.
    bOutOfBounds = (uAccessViolationAddress < oPageHeapAllocation.uAllocationStartAddress) \
                or (uAccessViolationAddress >= oPageHeapAllocation.uAllocationEndAddress);
  (sHeapBlockAndOffsetId, sHeapBlockAndOffsetDescription) = \
      ftsGetHeapBlockAndOffsetIdAndDescription(uAccessViolationAddress, oPageHeapAllocation);
  
  oBugReport.sBugDescription = "Access violation while %s %smemory at 0x%X; %s." % (sViolationTypeDescription, \
      oPageHeapAllocation.bFreed and "freed " or "", uAccessViolationAddress, sHeapBlockAndOffsetDescription);
  sPotentialRisk = {
    "R": "might allow information disclosure and (less likely) arbitrary code execution",
    "W": "indicates arbitrary code execution may be possible",
    "E": "indicates arbitrary code execution is very likely possible",
  }[sViolationTypeId];
  oBugReport.sSecurityImpact = "Potentially exploitable security issue that %s." % sPotentialRisk;
  if oPageHeapAllocation.bFreed:
    # --- (OOB)UAF -----------------------------------------------------------
    # We do not expect to see corruption of the page heap struct, as this should have been detected when the memory was
    # freed. The code may have tried to access data outside the bounds of the freed memory (double face-palm!).
    oBugReport.sBugTypeId = "UAF%s%s" % (sViolationTypeId, sHeapBlockAndOffsetId);
    oBugReport.sBugDescription += " This indicates a Use-After-Free (UAF) bug was triggered.";
    if bOutOfBounds:
      oBugReport.sBugTypeId = "OOB" + oBugReport.sBugTypeId;
      oBugReport.sBugDescription += " In addition, the code attempted to access data Out-Of-Bounds (OOB).";
    return;
  
  if bOutOfBounds:
    oBugReport.sBugTypeId = "OOB%s%s" % (sViolationTypeId, sHeapBlockAndOffsetId);
    oBugReport.sBugDescription += " This indicates an Out-Of-Bounds (OOB) access bug was triggered.";
  else:
    # TODO: add heap block access rights description!
    oBugReport.sBugTypeId = "AV%s%s" % (sViolationTypeId, sHeapBlockAndOffsetId);
    oBugReport.sBugDescription += " suggests an earlier memory corruption has corrupted a pointer, index or offset.";
  # We can check the page heap structures for signs of corruption to detect earlier out-of-bounds writes that did not
  # cause an access violation.
  oCorruptionDetector = oPageHeapAllocation.foCheckForCorruption();
  if oCorruptionDetector:
    # We detected a modified byte; there was an OOB write before the one that caused this access
    # violation. Use it's offset instead and add this fact to the description.
    if bGenerateReportHTML:
      oBugReport.atxMemoryRemarks.extend(oCorruptionDetector.fatxMemoryRemarks());
    uCorruptionStartAddress = oCorruptionDetector.uCorruptionStartAddress;
    sHeapBlockAndOffsetId, sHeapBlockAndOffsetDescription = ftsGetHeapBlockAndOffsetIdAndDescription(uCorruptionStartAddress, oPageHeapAllocation);
    # sHeapBlockAndOffsetDescription ^^^ is discarded because it repeats the heap block size, which is already mentioned
    # in oBugReport.sBugDescription
    if uCorruptionStartAddress <= oPageHeapAllocation.uBlockStartAddress:
      uOffsetBeforeStartOfBlock = oPageHeapAllocation.uBlockStartAddress - uCorruptionStartAddress;
      oBugReport.sBugDescription += (
        " An earlier out-of-bounds write was detected at 0x%X, %d/0x%X bytes " \
        "before that block because it modified the page heap prefix pattern."
      ) % (uCorruptionStartAddress, uOffsetBeforeStartOfBlock, uOffsetBeforeStartOfBlock);
    elif uCorruptionStartAddress >= oPageHeapAllocation.uBlockEndAddress:
      uOffsetBeyondEndOfBlock = uCorruptionStartAddress - oPageHeapAllocation.uBlockEndAddress;
      oBugReport.sBugDescription += (
        " An earlier out-of-bounds write was detected at 0x%X, %d/0x%X bytes " \
        "beyond that block because it modified the page heap suffix pattern."
      ) % (uCorruptionStartAddress, uOffsetBeyondEndOfBlock, uOffsetBeyondEndOfBlock);
    if uCorruptionStartAddress == oPageHeapAllocation.uBlockEndAddress:
      if sViolationTypeId == "R":
        oBugReport.sBugDescription += " This appears to be a classic linear read beyond the end of a buffer.";
        sSecurityImpact = "Potentially highly exploitable security issue that might allow information disclosure.";
      else:
        oBugReport.sBugDescription += " This appears to be a classic linear buffer-overrun vulnerability.";
        sSecurityImpact = "Potentially highly exploitable security issue that might allow arbitrary code execution.";
    asCorruptedBytes = oCorruptionDetector.fasCorruptedBytes();
    oBugReport.sBugDescription += " The following byte values were written to the corrupted area: %s." % \
        ", ".join(asCorruptedBytes);
    oBugReport.sBugTypeId = "OOBW%s%s" % (sHeapBlockAndOffsetId, oCorruptionDetector.fsCorruptionId());
    return;
  # --- OOB ---------------------------------------------------------------------
  # An out-of-bounds read on a page heap block that is allocated and has padding that happens in the padding or
  # immediately following it could be the result of sequentially reading an array. This means there may have been
  # earlier out-of-bounds reads that did not trigger an access violation:
  if sViolationTypeId == "R" \
    and oPageHeapAllocation.bPageHeap \
    and oPageHeapAllocation.bAllocated \
    and oPageHeapAllocation.uBlockEndAddress < oPageHeapAllocation.uAllocationEndAddress \
    and uAccessViolationAddress >= oPageHeapAllocation.uBlockEndAddress \
    and uAccessViolationAddress <= oPageHeapAllocation.uAllocationEndAddress:
    oBugReport.sBugDescription += " An earlier out-of-bounds read before this address may have happened without " \
          "having triggered an access violation.";

