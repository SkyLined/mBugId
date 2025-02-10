import hashlib;

from mWindowsAPI import fsHexNumber;

from ...dxConfig import dxConfig;
from ...fsGetNumberDescription import fsGetNumberDescription;
from ..iHeapManagerData import iHeapManagerData;
from .mPageHeapStructuresAndStaticValues import \
    bUseNewPageHeapStructures, \
    LIST_ENTRY32, LIST_ENTRY64, \
    DPH_BLOCK_INFORMATION32, DPH_BLOCK_INFORMATION64, \
    DPH_STATE_ALLOCATED, DPH_STATE_FREED, \
    uStartStampAllocated, uEndStampAllocated, \
    uStartStampFreed, uEndStampFreed, \
    uFreedHeapBlockFillByte, \
    uHeapBlockEndPaddingFillByte;
from .cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock import \
    cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock;

gbDebugOutput = False;

class cPageHeapManagerData(iHeapManagerData):
  bDebugOutput = gbDebugOutput;
  sType = "page heap";
  @classmethod
  def fo0GetForProcessAndAddressNearHeapBlock(cClass, *txArguments, **dxArguments):
    return cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock(cClass, *txArguments, **dxArguments);
  
  def __init__(oSelf,
    uPointerSize,
    uPageHeapBlockAddress,
    oPageHeapBlock,
    oHeapBlockVirtualAllocation,
    o0AllocationHeader,
    o0AllocationHeaderVirtualAllocation,
    uHeapBlockHeaderStartAddress,
    o0HeapBlockHeader,
    uHeapBlockEndPaddingSize,
  ):
    oSelf.uPointerSize = uPointerSize;
    
    oSelf.uPageHeapBlockAddress = uPageHeapBlockAddress;
    oSelf.oPageHeapBlock = oPageHeapBlock;
    oSelf.uPageHeapBlockEndAddress = uPageHeapBlockAddress + oPageHeapBlock.fuGetSize();
    oSelf.uPageHeapBlockSize = oSelf.uPageHeapBlockEndAddress - oSelf.uPageHeapBlockAddress;
    assert oSelf.uPageHeapBlockSize > 0, \
        "Cannot have a heap block of size %d0x%X" % (
          "-" if oSelf.uPageHeapBlockSize < 0 else "",
          abs(oSelf.uPageHeapBlockSize)
        );
    
    oSelf.oHeapBlockVirtualAllocation = oHeapBlockVirtualAllocation;
    
    oSelf.uHeapBlockStartAddress = oPageHeapBlock.pUserAllocation.fuGetValue();
    oSelf.uHeapBlockEndAddress = oSelf.uHeapBlockStartAddress + oPageHeapBlock.nUserRequestedSize.fuGetValue();
    oSelf.uHeapBlockSize = oPageHeapBlock.nUserRequestedSize.fuGetValue();
    
    oSelf.o0AllocationHeader = o0AllocationHeader;
    oSelf.o0AllocationHeaderVirtualAllocation = o0AllocationHeaderVirtualAllocation;
    if o0AllocationHeader:
      oSelf.uAllocationHeaderStartAddress = oHeapBlockVirtualAllocation.uStartAddress;
      oSelf.uAllocationHeaderEndAddress = oHeapBlockVirtualAllocation.uStartAddress + o0AllocationHeader.fuGetSize();
      oSelf.uAllocationHeaderSize = oSelf.uAllocationHeaderEndAddress - oSelf.uAllocationHeaderStartAddress;
    
    oSelf.o0HeapBlockHeader = o0HeapBlockHeader;
    if o0HeapBlockHeader:
      oSelf.u0HeapRootAddress = o0HeapBlockHeader.Heap.fuGetValue();
      oSelf.uHeapBlockHeaderStartAddress = uHeapBlockHeaderStartAddress;
      oSelf.o0HeapBlockHeader = o0HeapBlockHeader;
      oSelf.uHeapBlockHeaderEndAddress = uHeapBlockHeaderStartAddress + o0HeapBlockHeader.fuGetSize();
      oSelf.uHeapBlockHeaderSize = oSelf.uHeapBlockHeaderEndAddress - oSelf.uHeapBlockHeaderStartAddress;
      assert oSelf.uHeapBlockHeaderEndAddress == oSelf.uHeapBlockStartAddress, \
          "Page heap block header end address 0x%X should be the same as the heap block start address 0x%X" % \
          (oSelf.uHeapBlockHeaderEndAddress, oSelf.uHeapBlockStartAddress);
    else:
      oSelf.u0HeapRootAddress = None;
    if not bUseNewPageHeapStructures:
      oSelf.bAllocated = oPageHeapBlock.uState.fuGetValue() == DPH_STATE_ALLOCATED;
      oSelf.bFreed = oPageHeapBlock.uState.fuGetValue() == DPH_STATE_FREED;
    else:
      if o0HeapBlockHeader:
        oSelf.bAllocated = (
          o0HeapBlockHeader.StartStamp == uStartStampAllocated
          or o0HeapBlockHeader.EndStamp == uEndStampAllocated
        );
        oSelf.bFreed = (
          o0HeapBlockHeader.StartStamp == uStartStampFreed
          or o0HeapBlockHeader.EndStamp == uEndStampFreed
        );
        assert not oSelf.bAllocated or not oSelf.bFreed, \
            "\r\n".join([
              "Block is both allocated and freed!?",
              "DPH_BLOCK_INFORMATION:",
              "\r\n".join(o0HeapBlockHeader.fasDump()),
            ]);
      else:
        # This is an assumption.
        oSelf.bAllocated = False;
        oSelf.bFreed = True;
    
    if uHeapBlockEndPaddingSize:
      oSelf.uHeapBlockEndPaddingStartAddress = oSelf.uHeapBlockEndAddress;
      oSelf.uHeapBlockEndPaddingSize = uHeapBlockEndPaddingSize;
      oSelf.uHeapBlockEndPaddingEndAddress = oSelf.uHeapBlockEndAddress + uHeapBlockEndPaddingSize;
      assert oSelf.uHeapBlockEndPaddingEndAddress == oHeapBlockVirtualAllocation.uEndAddress, \
          "Page heap block end padding end address %s should be the same as the allocation end address %s" % (
            fsHexNumber(oSelf.uHeapBlockEndPaddingEndAddress),
            fsHexNumber(oHeapBlockVirtualAllocation.uEndAddress),
          );
    else:
      oSelf.uHeapBlockEndPaddingStartAddress = None;
      oSelf.uHeapBlockEndPaddingSize = None;
      oSelf.uHeapBlockEndPaddingEndAddress = None;
    
    oSelf.__d0uCorruptedByte_by_uAddress = None; # None means we haven't called `__fDetectCorruption` yet.
    oSelf.__uCorruptionStartAddress = None;
    oSelf.__uCorruptionEndAddress = None;
    
  @property
  def bCorruptionDetected(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    return len(oSelf.__d0uCorruptedByte_by_uAddress) > 0;
  
  @property
  def uCorruptionStartAddress(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    return oSelf.__uCorruptionStartAddress;
  
  @property
  def uCorruptionEndAddress(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    return oSelf.__uCorruptionEndAddress;
  
  @property
  def uMemoryDumpStartAddress(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    return oSelf.__uMemoryDumpStartAddress;
  
  @property
  def uMemoryDumpEndAddress(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    return oSelf.__uMemoryDumpEndAddress;
  
  @property
  def uMemoryDumpSize(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    return oSelf.__uMemoryDumpEndAddress - oSelf.__uMemoryDumpStartAddress;
  
  @property
  def sCorruptionId(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    assert oSelf.bCorruptionDetected, \
        "Cannot get a corruption id if no corruption was detected!";
    (sIgnoredSizeId, sCorruptionOffsetId, sCorruptionOffsetDescription, sIgnoredSizeDescription) = \
        oSelf.ftsGetIdAndDescriptionForAddress(oSelf.__uCorruptionStartAddress);
    # ^^^ sCorruptionOffsetDescription is not used.
    uCorruptionLength = oSelf.__uCorruptionEndAddress - oSelf.__uCorruptionStartAddress;
    sId = "%s~%s" % (sCorruptionOffsetId, fsGetNumberDescription(uCorruptionLength));
    # Only hash the chars when the bugid is not architecture independent, as different architectures may result in
    # different sized corruptions, which we can compensate for in the length, but not in the hash.
    if dxConfig["uArchitectureIndependentBugIdBits"] == 0 and dxConfig["uHeapCorruptedBytesHashChars"]:
      oHasher = hashlib.md5();
      uAddress = oSelf.__uCorruptionStartAddress;
      while uAddress < oSelf.__uCorruptionEndAddress:
        if uAddress in oSelf.__d0uCorruptedByte_by_uAddress:
          oHasher.update(bytes((oSelf.__d0uCorruptedByte_by_uAddress[uAddress],)));
        uAddress += 1;
      sId += "#%s" % oHasher.hexdigest()[:dxConfig["uHeapCorruptedBytesHashChars"]];
    return sId;
  
  def fuHeapBlockHeaderFieldAddress(oSelf, sFieldName, sSubFieldName = None):
    assert oSelf.o0HeapBlockHeader, \
        "Please make sure `.oSelf.o0HeapBlockHeader` is available before calling this method!";
    uAddress = oSelf.uHeapBlockHeaderStartAddress + oSelf.o0HeapBlockHeader.fuGetOffsetOfMember(sFieldName);
    if sSubFieldName:
      oField = getattr(oSelf.o0HeapBlockHeader, sFieldName);
      uAddress += oField.fuGetOffsetOfMember(sSubFieldName);
    return uAddress;
  
  def fuHeapBlockHeaderFieldSize(oSelf, sFieldName, sSubFieldName = None):
    assert oSelf.o0HeapBlockHeader, \
        "Please make sure `.oSelf.o0HeapBlockHeader` is available before calling this method!";
    oField = getattr(oSelf.o0HeapBlockHeader, sFieldName);
    if sSubFieldName:
      oField = getattr(oField, sSubFieldName);
    return oField.fuGetSize();
  
  def fatxGetMemoryRemarks(oSelf):
    if oSelf.__d0uCorruptedByte_by_uAddress is None:
      oSelf.__fDetectCorruption();
    atxMemoryRemarks = [
      ("Allocation start",                  oSelf.oHeapBlockVirtualAllocation.uStartAddress, None),
      ("Heap block start",                  oSelf.uHeapBlockStartAddress, None),
      ("Heap block end",                    oSelf.uHeapBlockEndAddress, None),
      ("Allocation end",                    oSelf.oHeapBlockVirtualAllocation.uEndAddress, None),
    ];
    if oSelf.o0AllocationHeader:
      atxMemoryRemarks += [
        ("Allocation header start",         oSelf.uAllocationHeaderStartAddress, None),
        ("Allocation header end",           oSelf.uAllocationHeaderEndAddress, None),
      ];
    if not oSelf.o0AllocationHeaderVirtualAllocation:
      atxMemoryRemarks += [
        ("Heap block allocation start", oSelf.oHeapBlockVirtualAllocation.uStartAddress, None),
        ("Heap block allocation size", oSelf.oHeapBlockVirtualAllocation.uSize, None),
      ];
    elif oSelf.o0AllocationHeaderVirtualAllocation.uStartAddress != oSelf.oHeapBlockVirtualAllocation.uStartAddress:
      atxMemoryRemarks += [
        ("Allocation header allocation start", oSelf.o0AllocationHeaderVirtualAllocation.uStartAddress, None),
        ("Allocation header allocation size", oSelf.o0AllocationHeaderVirtualAllocation.uSize, None),
        ("Heap block allocation start", oSelf.oHeapBlockVirtualAllocation.uStartAddress, None),
        ("Heap block allocation size", oSelf.oHeapBlockVirtualAllocation.uSize, None),
      ];
    else:
      atxMemoryRemarks += [
        ("Page Heap allocation start", oSelf.oHeapBlockVirtualAllocation.uStartAddress, None),
        ("Page Heap allocation size", oSelf.oHeapBlockVirtualAllocation.uSize, None),
      ];

    if oSelf.o0HeapBlockHeader:
      atxMemoryRemarks += [
        ("Page heap StartStamp",            oSelf.fuHeapBlockHeaderFieldAddress("StartStamp"), None),
        ("Page heap Heap",                  oSelf.fuHeapBlockHeaderFieldAddress("Heap"), None),
        ("Page heap RequestedSize",         oSelf.fuHeapBlockHeaderFieldAddress("RequestedSize"), None),
        ("Page heap ActualSize",            oSelf.fuHeapBlockHeaderFieldAddress("ActualSize"), None),
        ("Page heap StackTrace",            oSelf.fuHeapBlockHeaderFieldAddress("StackTrace"), None),
        ("Page heap EndStamp",              oSelf.fuHeapBlockHeaderFieldAddress("EndStamp"), None),
      ];
    if oSelf.uHeapBlockEndPaddingSize:
      atxMemoryRemarks += [
        ("Page heap allocation end padding", oSelf.uHeapBlockEndPaddingStartAddress, None),
      ];
    for (uAddress, uCorruptedByte) in oSelf.__d0uCorruptedByte_by_uAddress.items():
      atxMemoryRemarks += [
        ("Corrupted (should be %02X)" % uCorruptedByte, uAddress, None)
      ];
    return atxMemoryRemarks;
  
  def __fDetectCorruptionHelper(oSelf, uStartAddress, sbExpectedBytes, sbActualBytes, sDebugName):
    assert len(sbExpectedBytes) == len(sbActualBytes), \
        "Cannot compare %s expected bytes to %s actual bytes" % (
          fsHexNumber(len(sbExpectedBytes)),
          fsHexNumber(len(sbActualBytes))
        );
    au0ModifiedBytes = [];
    u0FirstDetectedCorruptionAddress = None;
    u0LastDetectedCorruptionAddress = None;
    for uIndex in range(len(sbExpectedBytes)):
      if sbActualBytes[uIndex] != sbExpectedBytes[uIndex]:
        au0ModifiedBytes.append(sbActualBytes[uIndex]);
        uAddress = uStartAddress + uIndex;
        if u0FirstDetectedCorruptionAddress is None:
          u0FirstDetectedCorruptionAddress = uAddress;
        u0LastDetectedCorruptionAddress = uAddress;
        if oSelf.__uCorruptionStartAddress is None or oSelf.__uCorruptionStartAddress > uAddress:
          oSelf.__uCorruptionStartAddress = uAddress;
        if oSelf.__uCorruptionEndAddress is None or oSelf.__uCorruptionEndAddress < uAddress + 1:
          oSelf.__uCorruptionEndAddress = uAddress + 1;
        oSelf.__d0uCorruptedByte_by_uAddress[uAddress] = sbExpectedBytes[uIndex];
        if uAddress < oSelf.__uMemoryDumpStartAddress:
          oSelf.__uMemoryDumpStartAddress = uAddress;
        if uAddress > oSelf.__uMemoryDumpEndAddress:
          oSelf.__uMemoryDumpEndAddress = uAddress;
      else:
        au0ModifiedBytes.append(None);
    if gbDebugOutput:
      if u0FirstDetectedCorruptionAddress is not None:
        print("│ × Corruption detected in %s [%s] @ %s" % (
          sDebugName,
          fsHexNumber(len(sbExpectedBytes)),
          fsHexNumber(uStartAddress),
        ));
        print("│   Expected:  %s" % " ".join(["%02X" % uByte for uByte in sbExpectedBytes]));
        print("│   Corrupt:   %s" % " ".join(["··" if u0Byte is None else ("%02X" % u0Byte) for u0Byte in au0ModifiedBytes]));
        print("│   Range:     %s-%s" % (
          fsHexNumber(u0FirstDetectedCorruptionAddress),
          fsHexNumber(u0LastDetectedCorruptionAddress + 1)
        ));
      else:
        print("│ √ No corruption in %s [%s] @ %s" % (
          sDebugName,
          fsHexNumber(len(sbExpectedBytes)),
          fsHexNumber(uStartAddress),
        ));
  
  def __fDetectCorruption(oSelf):
    oSelf.__d0uCorruptedByte_by_uAddress = {};
    if not oSelf.oHeapBlockVirtualAllocation.bAllocated or oSelf.o0HeapBlockHeader is None:
      if gbDebugOutput and oSelf.o0HeapBlockHeader is None: print("Corruption cannot be detected because heap block header was not found");
      # The heap block has been freed; we cannot detect corruption.
      oSelf.__uMemoryDumpStartAddress = None;
      oSelf.__uMemoryDumpEndAddress = None;
      return;
    if gbDebugOutput: print("┌─ Detecting corruption around page heap block [0x%X]@ 0x%X" % (oSelf.uHeapBlockSize, oSelf.uHeapBlockStartAddress));
    oSelf.__uMemoryDumpStartAddress = oSelf.uHeapBlockHeaderSize and oSelf.uHeapBlockHeaderStartAddress or oSelf.uHeapBlockStartAddress;
    oSelf.__uMemoryDumpEndAddress = oSelf.uHeapBlockEndPaddingSize and oSelf.uHeapBlockEndPaddingEndAddress or oSelf.uHeapBlockEndAddress;
    # Check the page heap block header
    DPH_BLOCK_INFORMATION = {4: DPH_BLOCK_INFORMATION32, 8: DPH_BLOCK_INFORMATION64}[oSelf.uPointerSize];
    LIST_ENTRY = {4: LIST_ENTRY32, 8: LIST_ENTRY64}[oSelf.uPointerSize];
    oExpectedHeapBlockHeader = DPH_BLOCK_INFORMATION(**dict([tx for tx in [
      ("StartStamp", uStartStampAllocated if oSelf.bAllocated else uStartStampFreed),
      ("PaddingStart", 0) if hasattr(oSelf.o0HeapBlockHeader, "PaddingStart") else None,
      ("Heap", oSelf.u0HeapRootAddress) if oSelf.u0HeapRootAddress is not None else None, # We do not always know the correct value
      ("RequestedSize", oSelf.oPageHeapBlock.nUserRequestedSize.fuGetValue()),
      ("ActualSize", oSelf.oHeapBlockVirtualAllocation.uSize),
      ("FreeQueue", oSelf.o0HeapBlockHeader.FreeQueue), # We do not know the correct value.
      ("StackTrace", oSelf.oPageHeapBlock.StackTrace),
      ("PaddingEnd", 0) if hasattr(oSelf.o0HeapBlockHeader, "PaddingEnd") else None,
      ("EndStamp", oSelf.bAllocated and uEndStampAllocated or uEndStampFreed),
    ] if tx]));
    sbExpectedBytes = oExpectedHeapBlockHeader.fsbGetValue();
    sbActualBytes = oSelf.o0HeapBlockHeader.fsbGetValue();
    oSelf.__fDetectCorruptionHelper(
      oSelf.uHeapBlockHeaderStartAddress,
      sbExpectedBytes,
      sbActualBytes,
      "page heap block header",
    );
    if oSelf.o0AllocationHeaderVirtualAllocation.fbContainsAddress(oSelf.oHeapBlockVirtualAllocation.uStartAddress):
      # The allocation header and the heap block header are in continuous memory.
      # We will check the bytes between the allocation header and the heap block
      # header; it should contain nothing but "\0"-s.
      uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderOffset = oSelf.uAllocationHeaderEndAddress - oSelf.oHeapBlockVirtualAllocation.uStartAddress;
      uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderSize = oSelf.uHeapBlockHeaderStartAddress - oSelf.uAllocationHeaderEndAddress;
      sbExpectedBytes = b"\0" * uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderSize;
      
      sb0ActualBytes = oSelf.oHeapBlockVirtualAllocation.fsbReadBytesStringForOffsetAndSize(
        uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderOffset,
        uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderSize,
      );
      assert sb0ActualBytes, \
          "Cannot read page heap data";
      oSelf.__fDetectCorruptionHelper(
        oSelf.uAllocationHeaderEndAddress,
        sbExpectedBytes,
        sb0ActualBytes,
        "padding between page heap allocation header and page heap block header",
      );
    else:
      # The allocation header and the heap block header are in different allocations.
      # We will check the empty space before the heap block header; it should contain
      # nothing but "\0"s
      uEmptySpaceBeforeHeapBlockHeaderSize = oSelf.uHeapBlockHeaderStartAddress - oSelf.oHeapBlockVirtualAllocation.uStartAddress;
      sbExpectedBytes = b"\0" * uEmptySpaceBeforeHeapBlockHeaderSize;
      
      sb0ActualBytes = oSelf.oHeapBlockVirtualAllocation.fsbReadBytesStringForOffsetAndSize(
        0,
        uEmptySpaceBeforeHeapBlockHeaderSize,
      );
      assert sb0ActualBytes, \
          "Cannot read page heap data";
      oSelf.__fDetectCorruptionHelper(
        oSelf.oHeapBlockVirtualAllocation.uStartAddress,
        sbExpectedBytes,
        sb0ActualBytes,
        "padding before page heap block header",
      );
    # Check the heap block if it is freed
    if not bUseNewPageHeapStructures and oSelf.bFreed:
      sbExpectedBytes = bytes((uFreedHeapBlockFillByte,)) * oSelf.uHeapBlockSize;
      sb0ActualBytes = oSelf.oHeapBlockVirtualAllocation.fsbReadBytesStringForOffsetAndSize(
        oSelf.uHeapBlockStartAddress - oSelf.oHeapBlockVirtualAllocation.uStartAddress,
        oSelf.uHeapBlockSize,
      );
      assert sb0ActualBytes, \
          "Cannot read page heap data";
      oSelf.__fDetectCorruptionHelper(
        oSelf.uHeapBlockStartAddress,
        sbExpectedBytes,
        sb0ActualBytes,
        "heap block",
      );
    # Check the allocation end padding
    if oSelf.uHeapBlockEndPaddingSize:
      sbExpectedBytes = bytes((uHeapBlockEndPaddingFillByte,)) * oSelf.uHeapBlockEndPaddingSize;
      sb0ActualBytes = oSelf.oHeapBlockVirtualAllocation.fsbReadBytesStringForOffsetAndSize(
        oSelf.uHeapBlockEndPaddingStartAddress - oSelf.oHeapBlockVirtualAllocation.uStartAddress,
        oSelf.uHeapBlockEndPaddingSize,
      );
      assert sb0ActualBytes, \
          "Cannot read page heap data";
      oSelf.__fDetectCorruptionHelper(
        oSelf.uHeapBlockEndPaddingStartAddress,
        sbExpectedBytes,
        sb0ActualBytes,
        "padding after heap block",
      );
    if gbDebugOutput:
      if oSelf.__uCorruptionStartAddress:
        print("└─ × Corruption detected in range %s-%s" % (
          fsHexNumber(oSelf.__uCorruptionStartAddress),
          fsHexNumber(oSelf.__uCorruptionEndAddress),
        ));
      else:
        print("└─ √ No corruption detected.");

  def __str__(oSelf):
    return "Page heap block: %s" % (
      ", ".join(
        "%s=%s" % (sName, fsHexNumber(uValue))
        for (sName, uValue, xIgnored) in oSelf.fatxGetMemoryRemarks()
      )
    );