from .ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress import ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress;

class cHeapManagerData(object):
  def __init__(oSelf,
    oVirtualAllocation,
    uHeapBlockStartAddress,
    uHeapBlockSize,
    bAllocated,
  ):
    oSelf.oVirtualAllocation = oVirtualAllocation;
    
    oSelf.uHeapBlockStartAddress = uHeapBlockStartAddress;
    oSelf.uHeapBlockSize = uHeapBlockSize;
    oSelf.uHeapBlockEndAddress = uHeapBlockStartAddress + uHeapBlockSize;
    
    oSelf.bAllocated = bAllocated;
    oSelf.bFreed = not bAllocated;
    
    oSelf.bCorruptionDetected = False;
    
    oSelf.uMemoryDumpStartAddress = uHeapBlockStartAddress - oSelf.uHeapBlockHeaderSize;
    oSelf.uMemoryDumpEndAddress = oSelf.uAllocationEndPaddingSize and oSelf.uAllocationEndPaddingEndAddress or oSelf.uHeapBlockEndAddress;
    oSelf.uMemoryDumpSize = oSelf.uMemoryDumpEndAddress - oSelf.uMemoryDumpStartAddress;
  
  def ftsGetIdAndDescriptionForAddress(oSelf, uAddress):
    return ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress(
      uBlockStartAddress = oSelf.uHeapBlockStartAddress,
      uBlockSize = oSelf.uHeapBlockSize,
      sBlockType = "heap",
      uAddress = uAddress,
    );
  
  def fatxMemoryRemarks(oSelf):
    return [tx for tx in [
      ("Allocation start", oSelf.oVirtualAllocation.uStartAddress, None),
      ("Heap block start", oSelf.uHeapBlockStartAddress, None),
      ("Heap block end", oSelf.uHeapBlockEndAddress, None),
      ("Allocation end", oSelf.oVirtualAllocation.uEndAddress, None),
    ] if tx];
