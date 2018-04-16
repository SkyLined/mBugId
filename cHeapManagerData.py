from .fsGetNumberDescription import fsGetNumberDescription;
from .fsNumberOfBytes import fsNumberOfBytes;

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
  
  def ftsGetHeapBlockIdAndDescription(oSelf):
    if oSelf.uHeapBlockSize is not None:
      sId = "[%s]" % fsGetNumberDescription(oSelf.uHeapBlockSize);
      sDescription = "a %s heap block at 0x%X" % (fsNumberOfBytes(oSelf.uHeapBlockSize), oSelf.uHeapBlockStartAddress);
    else:
      sId = "[?]";
      sDescription = "a heap block of unknown size at an unknown address between 0x%08X and 0x%08X" % \
          (oSelf.oVirtualAllocation.uStartAddress, oVirtualAllocation.uEndAddress);
    return (sId, sDescription);
  
  def ftsGetOffsetIdAndDescriptionForAddress(oSelf, uAddress):
    iOffsetFromStartOfHeapBlock = uAddress - oSelf.uHeapBlockStartAddress;
    if iOffsetFromStartOfHeapBlock < 0:
      sId = "-%s" % fsGetNumberDescription(-iOffsetFromStartOfHeapBlock, "-");
      sDescription = "%s before" % fsNumberOfBytes(-iOffsetFromStartOfHeapBlock);
    elif iOffsetFromStartOfHeapBlock < oSelf.uHeapBlockSize:
      sId = "@%s" % fsGetNumberDescription(iOffsetFromStartOfHeapBlock);
      if iOffsetFromStartOfHeapBlock == 0:
        sDescription = "at the start of";
      else:
        sDescription = "%s into" % fsNumberOfBytes(iOffsetFromStartOfHeapBlock);
    else:
      uOffsetBeyondEndOfHeapBlock = iOffsetFromStartOfHeapBlock - oSelf.uHeapBlockSize;
      sId = "+%s" % fsGetNumberDescription(uOffsetBeyondEndOfHeapBlock);
      if uOffsetBeyondEndOfHeapBlock == 0:
        sDescription = "at the end of";
      else:
        sDescription = "%s beyond" % fsNumberOfBytes(uOffsetBeyondEndOfHeapBlock);
    return (sId, sDescription);
  
  def fatxMemoryRemarks(oSelf):
    return [tx for tx in [
      ("Allocation start", oSelf.oVirtualAllocation.uStartAddress, None),
      ("Heap block start", oSelf.uHeapBlockStartAddress, None),
      ("Heap block end", oSelf.uHeapBlockEndAddress, None),
      ("Allocation end", oSelf.oVirtualAllocation.uEndAddress, None),
    ] if tx];
