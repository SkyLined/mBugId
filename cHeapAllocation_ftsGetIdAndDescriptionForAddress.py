from fsGetNumberDescription import fsGetNumberDescription;

def fsNumberOfBytes(uNumberOfBytes):
  if uNumberOfBytes == 1:
    return "1 byte";
  elif uNumberOfBytes < 10:
    return "%d bytes" % uNumberOfBytes;
  else:
    return "%d/0x%X bytes" % (uNumberOfBytes, uNumberOfBytes);

def cHeapAllocation_ftsGetIdAndDescriptionForAddress(oHeapAllocation, uAddress):
  if oHeapAllocation.uBlockStartAddress is None:
    # This must be a full page heap allocation; uAllocation* should be set.
    assert oHeapAllocation.uBlockSize is None, \
        "This is unexpected";
    iOffsetFromEndOfVirtualAllocation = uAddress - oHeapAllocation.uAllocationEndAddress;
    
    if iOffsetFromEndOfVirtualAllocation < 0:
      sId = "[?]#-%s" % fsGetNumberDescription(-iOffsetFromEndOfVirtualAllocation);
      sOffset = "%s before" % fsNumberOfBytes(-iOffsetFromEndOfVirtualAllocation);
    else:
      sId = "[?]#+%s" % fsGetNumberDescription(+iOffsetFromEndOfVirtualAllocation);
      sOffset = "%s beyond" % fsNumberOfBytes(iOffsetFromEndOfVirtualAllocation);
    sDescription = "%s the end of an allocation at 0x%X which used to contain a new freed heap block of unknown size" % \
        (sOffset, oHeapAllocation.uAllocationEndAddress);
  else:
    assert oHeapAllocation.uBlockSize is not None, \
        "This is unexpected";
    iOffsetFromStartOfHeapBlock = uAddress - oHeapAllocation.uBlockStartAddress;
    sId = "[%s]" % fsGetNumberDescription(oHeapAllocation.uBlockSize);
    if iOffsetFromStartOfHeapBlock < 0:
      sId += "-%s" % fsGetNumberDescription(-iOffsetFromStartOfHeapBlock, "-");
      sOffset = "%s before" % fsNumberOfBytes(-iOffsetFromStartOfHeapBlock);
    elif iOffsetFromStartOfHeapBlock < oHeapAllocation.uBlockSize:
      sId += "@%s" % fsGetNumberDescription(iOffsetFromStartOfHeapBlock);
      if iOffsetFromStartOfHeapBlock == 0:
        sOffset = "at the start of";
      else:
        sOffset = "%s into" % fsNumberOfBytes(iOffsetFromStartOfHeapBlock);
    else:
      uOffsetBeyondEndOfHeapBlock = iOffsetFromStartOfHeapBlock - oHeapAllocation.uBlockSize;
      sId += "+%s" % fsGetNumberDescription(uOffsetBeyondEndOfHeapBlock);
      if uOffsetBeyondEndOfHeapBlock == 0:
        sOffset = "at the end of";
      else:
        sOffset = "%s beyond" % fsNumberOfBytes(uOffsetBeyondEndOfHeapBlock);
    sDescription = "%s a %s heap block at 0x%X" % (sOffset, fsNumberOfBytes(oHeapAllocation.uBlockSize), oHeapAllocation.uBlockStartAddress);
  return (sId, sDescription);