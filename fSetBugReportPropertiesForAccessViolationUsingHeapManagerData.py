from dxConfig import dxConfig;
from fsGetNumberDescription import fsGetNumberDescription;
from ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;

def fSetBugReportPropertiesForAccessViolationUsingHeapManagerData(
  oBugReport,
  uAccessViolationAddress, sViolationTypeId, sViolationTypeDescription,
  oHeapManagerData,
  bGenerateReportHTML,
):
  if bGenerateReportHTML:
    uMemoryDumpStartAddress = oHeapManagerData.uMemoryDumpStartAddress;
    uMemoryDumpSize = oHeapManagerData.uMemoryDumpSize;
  if bGenerateReportHTML:
    if uAccessViolationAddress < oHeapManagerData.uHeapBlockStartAddress:
      uPrefix = oHeapManagerData.uHeapBlockStartAddress - uAccessViolationAddress;
      uMemoryDumpStartAddress -= uPrefix;
      uMemoryDumpSize += uPrefix;
      # If the memory dump because too large, truncate it.
      if uMemoryDumpSize > 0x1000:
        uMemoryDumpSize = 0x1000;
    elif uAccessViolationAddress >= oHeapManagerData.uHeapBlockEndAddress:
      uPostFix = uAccessViolationAddress - oHeapManagerData.uHeapBlockEndAddress + 1;
      # Show some of the guard page so we can insert labels where the AV took place, but only
      # if this does not cause the memory dump to become too large.
      if uMemoryDumpSize + uPostFix < 0x1000:
        uMemoryDumpSize += uPostFix;
    # Check if we're not trying to dump a rediculous amount of memory:
    # Clamp start and end address
    uMemoryDumpStartAddress, uMemoryDumpSize = ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(
      uAccessViolationAddress, oHeapManagerData.uPointerSize, uMemoryDumpStartAddress, uMemoryDumpSize
    );
    oBugReport.fAddMemoryDump(
      uMemoryDumpStartAddress,
      uMemoryDumpStartAddress + uMemoryDumpSize,
      "Memory near access violation at 0x%X" % uAccessViolationAddress,
    );
  bOutOfBounds = (uAccessViolationAddress < oHeapManagerData.uHeapBlockStartAddress) \
              or (uAccessViolationAddress >= oHeapManagerData.uHeapBlockEndAddress);
  (sHeapBlockAndOffsetId, sHeapBlockAndOffsetDescription) = \
      oHeapManagerData.ftsGetIdAndDescriptionForAddress(uAccessViolationAddress);
  
  oBugReport.sBugDescription = "Access violation while %s %smemory at 0x%X; %s." % (sViolationTypeDescription, \
      oHeapManagerData.bFreed and "freed " or "", uAccessViolationAddress, sHeapBlockAndOffsetDescription);
  sPotentialRisk = {
    "R": "might allow information disclosure and (less likely) arbitrary code execution",
    "W": "indicates arbitrary code execution may be possible",
    "E": "indicates arbitrary code execution is very likely possible",
  }[sViolationTypeId];
  oBugReport.sSecurityImpact = "Potentially exploitable security issue that %s." % sPotentialRisk;
  if oHeapManagerData.bFreed:
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
  # We may be able to check the heap manager structures for signs of corruption to detect earlier out-of-bounds writes
  # that overwrite them but did not cause an access violation.
  if oHeapManagerData.bCorruptionDetected:
    # We detected a modified byte; there was an OOB write before the one that caused this access
    # violation. Use it's offset instead and add this fact to the description.
    (sHeapBlockAndOffsetId, sHeapBlockAndOffsetDescription) = \
        oHeapManagerData.ftsGetIdAndDescriptionForAddress(oHeapManagerData.uCorruptionStartAddress);
    # sHeapBlockAndOffsetDescription ^^^ is discarded because it repeats the heap block size, which is already mentioned
    # in oBugReport.sBugDescription
    if oHeapManagerData.uCorruptionStartAddress <= oHeapManagerData.uHeapBlockStartAddress:
      uOffsetBeforeStartOfBlock = oHeapManagerData.uHeapBlockStartAddress - oHeapManagerData.uCorruptionStartAddress;
      oBugReport.sBugDescription += (
        " An earlier out-of-bounds write was detected at 0x%X, %d/0x%X bytes " \
        "before that block because it modified the page heap prefix pattern."
      ) % (oHeapManagerData.uCorruptionStartAddress, uOffsetBeforeStartOfBlock, uOffsetBeforeStartOfBlock);
    elif oHeapManagerData.uCorruptionStartAddress >= oHeapManagerData.uHeapBlockEndAddress:
      uOffsetBeyondEndOfBlock = oHeapManagerData.uCorruptionStartAddress - oHeapManagerData.uHeapBlockEndAddress;
      oBugReport.sBugDescription += (
        " An earlier out-of-bounds write was detected at 0x%X, %d/0x%X bytes " \
        "beyond that block because it modified the page heap suffix pattern."
      ) % (oHeapManagerData.uCorruptionStartAddress, uOffsetBeyondEndOfBlock, uOffsetBeyondEndOfBlock);
    if oHeapManagerData.uCorruptionStartAddress == oHeapManagerData.uHeapBlockEndAddress:
      if sViolationTypeId == "R":
        oBugReport.sBugDescription += " This appears to be a classic linear read beyond the end of a buffer.";
        sSecurityImpact = "Potentially highly exploitable security issue that might allow information disclosure.";
      else:
        oBugReport.sBugDescription += " This appears to be a classic linear buffer-overrun vulnerability.";
        sSecurityImpact = "Potentially highly exploitable security issue that might allow arbitrary code execution.";
    oBugReport.sBugTypeId = "OOBW%s%s" % (sHeapBlockAndOffsetId, oHeapManagerData.sCorruptionId);
    return;
  # --- OOB ---------------------------------------------------------------------
  # An out-of-bounds read on a heap block that is allocated and has padding that happens in or immedaitely after this 
  # padding could be the result of a sequential read where earlier out-of-bound reads of (parts of) this padding did
  # not trigger an access violation:
  if sViolationTypeId == "R" \
    and oHeapManagerData.bAllocated \
    and oHeapManagerData.uHeapBlockEndPaddingSize \
    and uAccessViolationAddress >= oHeapManagerData.uHeapBlockEndAddress \
    and uAccessViolationAddress <= oHeapManagerData.oVirtualAllocation.uEndAddress:
    oBugReport.sBugDescription += " An earlier out-of-bounds read before this address may have happened without " \
          "having triggered an access violation.";

