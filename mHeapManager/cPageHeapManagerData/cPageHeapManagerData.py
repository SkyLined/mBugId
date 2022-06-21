import hashlib;

from mWindowsSDK import PAGE_NOACCESS, PAGE_READWRITE;

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
from .cPageHeapManagerData_fo0CreateHelper import \
    cPageHeapManagerData_fo0CreateHelper;
#from .cPageHeapManagerData_fo0GetForProcessAndAllocationInformationStartAddress import \
#    cPageHeapManagerData_fo0GetForProcessAndAllocationInformationStartAddress;
from .cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock import \
    cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock;
from .cPageHeapManagerData_fo0GetForProcessAndPageHeapBlockStartAddress import \
    cPageHeapManagerData_fo0GetForProcessAndPageHeapBlockStartAddress;

gbDebugOutput = True;

class cPageHeapManagerData(iHeapManagerData):
  sType = "page heap";
  @classmethod
  def fo0CreateHelper(cClass, *txArguments, **dxArguments):
    return cPageHeapManagerData_fo0CreateHelper(cClass, *txArguments, **dxArguments);
#  @classmethod
#  def fo0GetForProcessAndAllocationInformationStartAddress(cClass, *txArguments, **dxArguments):
#    return cPageHeapManagerData_fo0GetForProcessAndAllocationInformationStartAddress(cClass, *txArguments, **dxArguments);
  @classmethod
  def fo0GetForProcessAndAddressNearHeapBlock(cClass, *txArguments, **dxArguments):
    return cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock(cClass, *txArguments, **dxArguments);
  @classmethod
  def fo0GetForProcessAndPageHeapBlockStartAddress(cClass, *txArguments, **dxArguments):
    return cPageHeapManagerData_fo0GetForProcessAndPageHeapBlockStartAddress(cClass, *txArguments, **dxArguments);
  
  def __init__(oSelf,
    uPointerSize,
    uPageHeapBlockAddress,
    oPageHeapBlock,
    oHeapBlockVirtualAllocation,
    o0AllocationHeader,
    uHeapBlockHeaderStartAddress,
    o0HeapBlockHeader,
    uHeapBlockEndPaddingSize,
  ):
    oSelf.uHeapRootAddress = None;
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
    if o0AllocationHeader:
      oSelf.uAllocationHeaderStartAddress = oHeapBlockVirtualAllocation.uStartAddress;
      oSelf.uAllocationHeaderEndAddress = oHeapBlockVirtualAllocation.uStartAddress + o0AllocationHeader.fuGetSize();
      oSelf.uAllocationHeaderSize = oSelf.uAllocationHeaderEndAddress - oSelf.uAllocationHeaderStartAddress;
    
    oSelf.o0HeapBlockHeader = o0HeapBlockHeader;
    if o0HeapBlockHeader:
      oSelf.uHeapBlockHeaderStartAddress = uHeapBlockHeaderStartAddress;
      oSelf.o0HeapBlockHeader = o0HeapBlockHeader;
      oSelf.uHeapBlockHeaderEndAddress = uHeapBlockHeaderStartAddress + o0HeapBlockHeader.fuGetSize();
      oSelf.uHeapBlockHeaderSize = oSelf.uHeapBlockHeaderEndAddress - oSelf.uHeapBlockHeaderStartAddress;
      assert oSelf.uHeapBlockHeaderEndAddress == oSelf.uHeapBlockStartAddress, \
          "Page heap block header end address 0x%X should be the same as the heap block start address 0x%X" % \
          (oSelf.uHeapBlockHeaderEndAddress, oSelf.uHeapBlockStartAddress);
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
          "Page heap block end padding end address 0x%X should be the same as the allocation end address 0x%X" % \
          (oSelf.uHeapBlockEndPaddingEndAddress, oHeapBlockVirtualAllocation.uEndAddress);
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
    # different sixed corruptions, which we can compensate for in the length, but not in the hash.
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
  
  def fatxMemoryRemarks(oSelf):
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
        "Cannot compare %d expected bytes to %d actual bytes" % (len(sbExpectedBytes), len(sbActualBytes));
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
        print("│ × Corruption detected in %s [0x%X] @ 0x%X" % (sDebugName, len(sbExpectedBytes), uStartAddress));
        print("│   Expected:  %s" % " ".join(["%02X" % uByte for uByte in sbExpectedBytes]));
        print("│   Corrupt:   %s" % " ".join(["··" if u0Byte is None else ("%02X" % u0Byte) for u0Byte in au0ModifiedBytes]));
        print("│   Range:     0x%X-0x%X" % (u0FirstDetectedCorruptionAddress, u0LastDetectedCorruptionAddress + 1));
      else:
        print("│ √ No corruption in %s [0x%X] @ 0x%X" % (sDebugName, len(sbExpectedBytes), uStartAddress));
  
  def __fDetectCorruption(oSelf):
    oSelf.__d0uCorruptedByte_by_uAddress = {};
    if not oSelf.oHeapBlockVirtualAllocation.bAllocated or oSelf.o0HeapBlockHeader is None:
      if gbDebugOutput and oSelf.o0HeapBlockHeader is None: print("Corruption cannnot be detected because heap block header was not found");
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
      ("Heap", oSelf.uHeapRootAddress or oSelf.o0HeapBlockHeader.Heap), # We do not always know the correct value
      ("RequestedSize", oSelf.oPageHeapBlock.nUserRequestedSize.fuGetValue()),
      ("ActualSize", oSelf.oHeapBlockVirtualAllocation.uSize),
      ("FreeQueue", oSelf.o0HeapBlockHeader.FreeQueue), # We do not know the correct value.
      ("StackTrace", oSelf.oPageHeapBlock.StackTrace),
      ("PaddingEnd", 0) if hasattr(oSelf.o0HeapBlockHeader, "PaddingEnd") else None,
      ("EndStamp", oSelf.bAllocated and uEndStampAllocated or uEndStampFreed),
    ] if tx]));
    sbExpectedBytes = oExpectedHeapBlockHeader.fsbGetValue();
    sbActualBytes = oSelf.o0HeapBlockHeader.fsbGetValue();
    oSelf.__fDetectCorruptionHelper(oSelf.uHeapBlockHeaderStartAddress, sbExpectedBytes, sbActualBytes, "page heap block header");
    # Check the empty space between the allocation header and the heap block header; it should contain nothing but "\0"s
    uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderOffset = oSelf.uAllocationHeaderEndAddress - oSelf.oHeapBlockVirtualAllocation.uStartAddress;
    uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderSize = oSelf.uHeapBlockHeaderStartAddress - oSelf.uAllocationHeaderEndAddress;
    sbExpectedBytes = b"\0" * uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderSize;
    
    sb0ActualBytes = oSelf.oHeapBlockVirtualAllocation.fsbReadBytesStringForOffsetAndSize(
      uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderOffset,
      uEmptySpaceBetweenAllocationHeaderAndHeapBlockHeaderSize,
    );
    assert sb0ActualBytes, \
        "Cannot read page heap data";
    oSelf.__fDetectCorruptionHelper(oSelf.uAllocationHeaderEndAddress, sbExpectedBytes, sb0ActualBytes, "padding after page heap block header")
    # Check the heap block if it is freed
    if not bUseNewPageHeapStructures and oSelf.bFreed:
      sbExpectedBytes = bytes((uFreedHeapBlockFillByte,)) * oSelf.uHeapBlockSize;
      sb0ActualBytes = oSelf.oHeapBlockVirtualAllocation.fsbReadBytesStringForOffsetAndSize(
        oSelf.uHeapBlockStartAddress - oSelf.oHeapBlockVirtualAllocation.uStartAddress,
        oSelf.uHeapBlockSize,
      );
      assert sb0ActualBytes, \
          "Cannot read page heap data";
      oSelf.__fDetectCorruptionHelper(oSelf.uHeapBlockStartAddress, sbExpectedBytes, sb0ActualBytes, "heap block");
    # Check the allocation end padding
    if oSelf.uHeapBlockEndPaddingSize:
      sbExpectedBytes = bytes((uHeapBlockEndPaddingFillByte,)) * oSelf.uHeapBlockEndPaddingSize;
      sb0ActualBytes = oSelf.oHeapBlockVirtualAllocation.fsbReadBytesStringForOffsetAndSize(
        oSelf.uHeapBlockEndPaddingStartAddress - oSelf.oHeapBlockVirtualAllocation.uStartAddress,
        oSelf.uHeapBlockEndPaddingSize,
      );
      assert sb0ActualBytes, \
          "Cannot read page heap data";
      oSelf.__fDetectCorruptionHelper(oSelf.uHeapBlockEndPaddingStartAddress, sbExpectedBytes, sb0ActualBytes, "padding after heap block");
    if gbDebugOutput:
      if oSelf.__uCorruptionStartAddress:
        print("└─ × Corruption detected in range 0x%X-0x%X" % (oSelf.__uCorruptionStartAddress, oSelf.__uCorruptionEndAddress));
      else:
        print("└─ √ No corruption detected.");

  def __str__(oSelf):
    return "Page heap block: %s" % (
      ", ".join(
        "%s=0x%X" % (sName, uValue)
        for (sName, uValue, xIgnored) in oSelf.fatxMemoryRemarks()
      )
    );