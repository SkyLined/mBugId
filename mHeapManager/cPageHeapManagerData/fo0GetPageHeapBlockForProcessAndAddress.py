from mWindowsAPI import cVirtualAllocation, fsHexNumber;

from .mPageHeapStructuresAndStaticValues import (
  DPH_HEAP_BLOCK32,
  DPH_HEAP_BLOCK64,
);

def fo0GetPageHeapBlockForProcessAndAddress(oProcess, uPageHeapBlockStartAddress, bDebugOutput = False):
  # DPH_HEAP_BLOCK structures are stored sequentially in a virtual allocation.
  oPageHeapBlockVirtualAllocation = cVirtualAllocation(
    uProcessId = oProcess.uId,
    uAddress = uPageHeapBlockStartAddress,
  );
  if not oPageHeapBlockVirtualAllocation.bAllocated:
    if bDebugOutput: print(
      "cPageHeapManagerData fo0GetPageHeapBlockForProcessAndAddress: "\
      "no memory allocated at page heap block address %s." % (
      fsHexNumber(uPageHeapBlockStartAddress),
    ));
    # The memory for this heap block has been freed: we cannot determine the
    # location for the DPH_ALLOCATION_HEADER structure, and thus cannot
    # provide any result.
    return None;
  # Try to read the page heap allocation information
  DPH_HEAP_BLOCK = {4: DPH_HEAP_BLOCK32, 8: DPH_HEAP_BLOCK64}[oProcess.uPointerSize]; 
  o0PageHeapBlock = oProcess.fo0ReadStructureForAddress(
    DPH_HEAP_BLOCK,
    uPageHeapBlockStartAddress,
  );
  if bDebugOutput:
    if o0PageHeapBlock:
      print(
        "cPageHeapManagerData fo0GetPageHeapBlockForProcessAndAddress: " \
        "page heap block:"
      );
      print(("┌─ DPH_HEAP_BLOCK ").ljust(80, "─"));
      for sLine in o0PageHeapBlock.fasDump():
        print("│ %s" % sLine);
      print("└".ljust(80, "─"));
    else:
      print(
        "cPageHeapManagerData fo0GetPageHeapBlockForProcessAndAddress: " \
        "page heap block vould not be read from address %s." % (
          fsHexNumber(uPageHeapBlockStartAddress),
        )
      );
  return o0PageHeapBlock;
