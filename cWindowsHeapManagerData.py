from cHeapManagerData import cHeapManagerData;

class cWindowsHeapManagerData(cHeapManagerData):
  def __init__(oSelf,
    oVirtualAllocation,
    uHeapEntryStartAddress,
    uHeapEntrySize,
    uHeapBlockStartAddress,
    uHeapBlockSize,
    bAllocated,
  ):
    oSelf.oVirtualAllocation = oVirtualAllocation;
    
    oSelf.uHeapEntryStartAddress = uHeapEntryStartAddress;
    oSelf.uHeapEntrySize = uHeapEntrySize;
    oSelf.uHeapEntryEndAddress = uHeapEntryStartAddress + uHeapEntrySize;
    
    oSelf.uHeapBlockStartAddress = uHeapBlockStartAddress;
    oSelf.uHeapBlockSize = uHeapBlockSize;
    oSelf.uHeapBlockEndAddress = uHeapBlockStartAddress + uHeapBlockSize;
    
    oSelf.bAllocated = bAllocated;
    oSelf.bFreed = not bAllocated;
    
    oSelf.bCorruptionDetected = False;
    
    if oSelf.uHeapEntrySize and oSelf.uHeapEntryEndAddress == uHeapBlockStartAddress:
      # The heap entry is right before the heap block; include both in the dump
      oSelf.uMemoryDumpStartAddress = uHeapEntryStartAddress;
      oSelf.uMemoryDumpEndAddress = oSelf.uHeapBlockEndAddress;
    else:
      oSelf.uMemoryDumpStartAddress = uHeapBlockStartAddress;
      oSelf.uMemoryDumpEndAddress = oSelf.uHeapBlockEndAddress;
    # Convenience
    oSelf.uMemoryDumpSize = oSelf.uMemoryDumpEndAddress - oSelf.uMemoryDumpStartAddress;
  
  def fatxMemoryRemarks(oSelf):
    return [tx for tx in [
      ("Allocation start", oSelf.oVirtualAllocation.uStartAddress, None),
      oSelf.uHeapBlockHeaderSize and 
          ("Heap block header start", oSelf.uHeapBlockHeaderStartAddress, None),
      oSelf.uHeapBlockHeaderSize and 
          ("Heap block header end", oSelf.uHeapBlockHeaderEndAddress, None),
      ("Heap block start", oSelf.uHeapBlockStartAddress, None),
      ("Heap block end", oSelf.uHeapBlockEndAddress, None),
      ("Allocation end", oSelf.oVirtualAllocation.uEndAddress, None),
    ] if tx];