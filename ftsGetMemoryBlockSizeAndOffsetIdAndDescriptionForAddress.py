from .fsGetNumberDescription import fsGetNumberDescription;
from .fsNumberOfBytes import fsNumberOfBytes;

def ftsGetMemoryBlockSizeAndOffsetIdAndDescriptionForAddress(uBlockStartAddress, uBlockSize, sBlockType, uAddress):
  sSizeId = "[%s]" % fsGetNumberDescription(uBlockSize);
  sSizeDescription = "a %s %s block at 0x%X" % (fsNumberOfBytes(uBlockSize), sBlockType, uBlockStartAddress);
  
  iOffsetFromStartOfBlock = uAddress - uBlockStartAddress;
  if iOffsetFromStartOfBlock < 0:
    # "-X" means at X bytes before the block
    sOffsetId = "-%s" % fsGetNumberDescription(-iOffsetFromStartOfBlock, "-");
    sOffsetDescription = "%s before" % fsNumberOfBytes(-iOffsetFromStartOfBlock);
  else:
    iOffsetFromEndOfBlock = iOffsetFromStartOfBlock - uBlockSize;
    if iOffsetFromEndOfBlock < 0:
      # "@X" means at X bytes within the block
      sOffsetId = "@%s" % fsGetNumberDescription(iOffsetFromStartOfBlock);
      if iOffsetFromStartOfBlock == 0:
        sOffsetDescription = "at the start of";
      else:
        sOffsetDescription = "%s into" % fsNumberOfBytes(iOffsetFromStartOfBlock);
    else:
      # "+X" means X bytes beyond the block
      sOffsetId = "+%s" % fsGetNumberDescription(iOffsetFromEndOfBlock);
      if iOffsetFromEndOfBlock == 0:
        sOffsetDescription = "at the end of";
      else:
        sOffsetDescription = "%s beyond" % fsNumberOfBytes(iOffsetFromEndOfBlock);
  return (sSizeId, sOffsetId, sOffsetDescription, sSizeDescription);
