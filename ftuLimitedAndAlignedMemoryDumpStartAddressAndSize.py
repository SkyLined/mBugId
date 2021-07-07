from .dxConfig import dxConfig;

# This code:
# 1) limits memory dumps to reasonable sizes by moving the start and/or end address, while making sure the memory
#    around the most interesting address is always in the dump, preferably near the middle.
# 2) Rounds the start address down and the size up to align both with the pointer size of the ISA.
def ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(uMostInterestingAddress, uPointerSize, uMemoryDumpStartAddress, uMemoryDumpSize): 
  # Calculate start and end address aligned to pointer size:
  uMemoryDumpEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize;
  uPointerSizeMask = uPointerSize - 1;
  uMemoryDumpStartAddress -= uMemoryDumpStartAddress & uPointerSizeMask; # decrease to align
  if uMemoryDumpEndAddress & uPointerSizeMask:
    uMemoryDumpEndAddress -= uMemoryDumpStartAddress & uPointerSizeMask; # decrease to align
    uMemoryDumpEndAddress += uPointerSize; # increase again to include original end address.
  # Recalculate the size of the memory area to be dumped:
  uMemoryDumpSize = uMemoryDumpEndAddress - uMemoryDumpStartAddress;

  if uMemoryDumpSize > dxConfig["uMaxMemoryDumpSize"]:
    # Yes, we'll need to reduce the size of the memory dump; try to find out what parts are farthest away
    # from the exception address and remove those. uMemoryDumpStartAddress and/or uMemoryDumpSize are updated.
    uMemoryDumpSizeBeforeMostInterestingAddress = uMostInterestingAddress - uMemoryDumpStartAddress;
    uMemoryDumpSizeAfterMostInterestingAddress = uMemoryDumpEndAddress - uMostInterestingAddress;
    # Regardless of where we remove bytes from the dump, the size will become the maximum size:
    uMemoryDumpSize = dxConfig["uMaxMemoryDumpSize"];
    if uMemoryDumpSizeBeforeMostInterestingAddress < dxConfig["uMaxMemoryDumpSize"] / 2:
      # The size before the address is reasonable: by reducing the total size, we reduced the size after the
      # address and the end address must be updated:
      uMemoryDumpEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize;
    elif uMemoryDumpSizeAfterMostInterestingAddress < dxConfig["uMaxMemoryDumpSize"] / 2:
      # The size after the address is reasonable: reduce the size before the address by increasing the start
      # address so that the dump still ends at the same address after having reduced its size:
      uMemoryDumpStartAddress = uMemoryDumpEndAddress - uMemoryDumpSize;
    else:
      # The size before and after the address are both too large: the memory dump will have the most interesting
      # address in the middle.
      uMemoryDumpStartAddress = int(round(uMostInterestingAddress - dxConfig["uMaxMemoryDumpSize"] / 2));
      # Align new start address:
      uMemoryDumpStartAddress -= uMemoryDumpStartAddress & uPointerSizeMask; # decrease to align
      uMemoryDumpEndAddress = uMemoryDumpStartAddress + uMemoryDumpSize;
  assert uMemoryDumpStartAddress + uMemoryDumpSize == uMemoryDumpEndAddress, \
      "Math is wrong: 0x%X + 0x%X != 0x%X" % (uMemoryDumpStartAddress, uMemoryDumpSize, uMemoryDumpEndAddress);
  assert uMemoryDumpSize <= dxConfig["uMaxMemoryDumpSize"], \
      "Math is wrong: memory dump size (0x%X) is larger than the maximum (0x%X)" % (uMemoryDumpSize, dxConfig["uMaxMemoryDumpSize"]);
  # return updated, aligned start address and limited, algned size
  return uMemoryDumpStartAddress, uMemoryDumpSize;

