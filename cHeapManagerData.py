from fsGetNumberDescription import fsGetNumberDescription;
from fsNumberOfBytes import fsNumberOfBytes;

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
    
    oSelf.uMemoryDumpStartAddress = oSelf.uHeapBlockHeaderSize and uHeapBlockHeaderStartAddress or uHeapBlockStartAddress;
    oSelf.uMemoryDumpEndAddress = oSelf.uAllocationEndPaddingSize and oSelf.uAllocationEndPaddingEndAddress or oSelf.uHeapBlockEndAddress;
    oSelf.uMemoryDumpSize = oSelf.uMemoryDumpEndAddress - oSelf.uMemoryDumpStartAddress;
  
  def ftsGetIdAndDescription(oSelf):
    sId = "[%s]" % fsGetNumberDescription(oSelf.uHeapBlockSize);
    sDescription = "a %s heap block at 0x%X" % (fsNumberOfBytes(oSelf.uHeapBlockSize), oSelf.uHeapBlockStartAddress);
    return (sId, sDescription);
  
  def ftsGetIdAndDescriptionForAddress(oSelf, uAddress):
    sId = "[%s]" % fsGetNumberDescription(oSelf.uHeapBlockSize);
    iOffsetFromStartOfHeapBlock = uAddress - oSelf.uHeapBlockStartAddress;
    if iOffsetFromStartOfHeapBlock < 0:
      sId += "-%s" % fsGetNumberDescription(-iOffsetFromStartOfHeapBlock, "-");
      sOffset = "%s before" % fsNumberOfBytes(-iOffsetFromStartOfHeapBlock);
    elif iOffsetFromStartOfHeapBlock < oSelf.uHeapBlockSize:
      sId += "@%s" % fsGetNumberDescription(iOffsetFromStartOfHeapBlock);
      if iOffsetFromStartOfHeapBlock == 0:
        sOffset = "at the start of";
      else:
        sOffset = "%s into" % fsNumberOfBytes(iOffsetFromStartOfHeapBlock);
    else:
      uOffsetBeyondEndOfHeapBlock = iOffsetFromStartOfHeapBlock - oSelf.uHeapBlockSize;
      sId += "+%s" % fsGetNumberDescription(uOffsetBeyondEndOfHeapBlock);
      if uOffsetBeyondEndOfHeapBlock == 0:
        sOffset = "at the end of";
      else:
        sOffset = "%s beyond" % fsNumberOfBytes(uOffsetBeyondEndOfHeapBlock);
    sDescription = "%s a %s heap block at 0x%X" % (sOffset, fsNumberOfBytes(oSelf.uHeapBlockSize), oSelf.uHeapBlockStartAddress);
    return (sId, sDescription);
  
  def fatxMemoryRemarks(oSelf):
    return [tx for tx in [
      ("Allocation start", oSelf.oVirtualAllocation.uStartAddress, None),
      ("Heap block start", oSelf.uHeapBlockStartAddress, None),
      ("Heap block end", oSelf.uHeapBlockEndAddress, None),
      ("Allocation end", oSelf.oVirtualAllocation.uEndAddress, None),
    ] if tx];
