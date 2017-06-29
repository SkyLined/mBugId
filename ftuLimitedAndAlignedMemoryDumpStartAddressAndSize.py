from dxConfig import dxConfig;

# This code:
# 1) limits memory dumps to reasonable sizes by moving the start and/or end address, while making sure the memory
#    around the most interesting address is always in the dump, preferably near the middle.
# 2) Rounds the start address down and the size up to align both with the pointer size of the ISA.
def ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(uMostInterestingAddress, uPointerSize, uMemoryDumpStartAddress, uMemoryDumpSize): 
  uMemoryDumpEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize;
  if uMemoryDumpSize > dxConfig["uMaxMemoryDumpSize"]:
    # Yes, we'll need to reduce the size of the memory dump; try to find out what parts are farthest away
    # from the exception address and remove those. uMemoryDumpStartAddress and/or uMemoryDumpSize are updated.
    uMemoryDumpSizeBeforeAddress = uMostInterestingAddress - uMemoryDumpStartAddress;
    uMemoryDumpSizeAfterAddress = uMemoryDumpEndAddress - uMostInterestingAddress;
    # Regardless of where we remove bytes from the dump, the size will become the maximum size:
    uMemoryDumpSize = dxConfig["uMaxMemoryDumpSize"];
    if uMemoryDumpSizeBeforeAddress < dxConfig["uMaxMemoryDumpSize"] / 2:
      # The size before the address is reasonable: by reducing the total size, we reduced the size after the
      # address and the end address must be updated:
      uMemoryDumpEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize;
    elif uMemoryDumpSizeAfterAddress < dxConfig["uMaxMemoryDumpSize"] / 2:
      # The size after the address is reasonable: reduce the size before the address by increasing the start
      # address so that the dump still ends at the same address after having reduced its size:
      uMemoryDumpStartAddress = uMemoryDumpEndAddress - dxConfig["uMaxMemoryDumpSize"];
    else:
      # The size before and after the address are both too large: increase the start address so that the dump
      # will surround that address as best as possible and reduce the end address to match.
      uMemoryDumpStartAddress = long(round(uMostInterestingAddress - dxConfig["uMaxMemoryDumpSize"] / 2));
      uMemoryDumpEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize;
  # Align start and end address to pointer size:
  uPointerSizeMask = uPointerSize - 1;
  uMemoryDumpStartAddress -= uMemoryDumpStartAddress & uPointerSizeMask; # decrease to align
  uMemoryDumpSize = uMemoryDumpEndAddress - uMemoryDumpStartAddress;
  uMemoryDumpNonAlignedSize = uMemoryDumpSize & uPointerSizeMask;
  if uMemoryDumpNonAlignedSize:
    uMemoryDumpSize += uPointerSize - uMemoryDumpNonAlignedSize; # increase to align.
  # return updated, aligned start address and limited, algned size
  return uMemoryDumpStartAddress, uMemoryDumpSize;

