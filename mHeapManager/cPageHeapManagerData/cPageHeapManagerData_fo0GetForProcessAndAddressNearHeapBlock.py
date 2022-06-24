from mWindowsSDK import PAGE_NOACCESS, PAGE_READWRITE;

from .fo0GetAllocationHeaderForVirtualAllocationAndPointerSize import \
    fo0GetAllocationHeaderForVirtualAllocationAndPointerSize;
from .fo0GetPageHeapBlockForProcessAndAddress import \
    fo0GetPageHeapBlockForProcessAndAddress;

gbDebugOutput = False;

def cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock(
  cClass,
  oProcess,
  uAddressNearHeapBlock,
  u0HeapBlockSize = None,
):
  o0HeapBlockVirtualAllocation = oProcess.fo0GetVirtualAllocationForAddressNearHeapBlock(uAddressNearHeapBlock);
  if not o0HeapBlockVirtualAllocation:
    return None;
  # What can happen for larger allocations is that the page heap header is not part of the
  # Virtual Allocation returned if you query an address inside the heap block. In this case
  # you can get a Virtual Allocation that includes it if you query the address of the byte
  # right before the heap block:
  if u0HeapBlockSize is not None and o0HeapBlockVirtualAllocation.uSize == u0HeapBlockSize:
    o0PreviousHeapBlockVirtualAllocation = oProcess.fo0GetVirtualAllocationForAddressNearHeapBlock(
      o0HeapBlockVirtualAllocation.uStartAddress - 1,
    );
    if not o0PreviousHeapBlockVirtualAllocation:
      if gbDebugOutput: print("cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "No virtual allocation before %s\r\n  expected heap block size 0x%X is assumed to be incorrect." % (
        o0HeapBlockVirtualAllocation,
        u0HeapBlockSize,
      ));
    elif o0PreviousHeapBlockVirtualAllocation.uEndAddress < o0HeapBlockVirtualAllocation.uEndAddress:
      if gbDebugOutput: print("cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: "\
        "Virtual allocation %s does not wrap %s\r\n  expected heap block size 0x%X is assumed to be incorrect." % (
        o0PreviousHeapBlockVirtualAllocation,
        o0HeapBlockVirtualAllocation,
        u0HeapBlockSize,
      ));
    else:
      o0AllocationHeader = fo0GetAllocationHeaderForVirtualAllocationAndPointerSize(
        o0PreviousHeapBlockVirtualAllocation,
        oProcess.uPointerSize,
      );
      if o0AllocationHeader:
        if gbDebugOutput: print("cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
          "Virtual allocation %s wraps %s and contains page heap header" % (
          o0PreviousHeapBlockVirtualAllocation,
          o0HeapBlockVirtualAllocation,
        ));
        o0HeapBlockVirtualAllocation = o0PreviousHeapBlockVirtualAllocation;
      else:
        if gbDebugOutput: print("cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
          "Virtual allocation %s wraps %s but does not contain page heap header" % (
          o0PreviousHeapBlockVirtualAllocation,
          o0HeapBlockVirtualAllocation,
        ));

  oHeapBlockVirtualAllocation = o0HeapBlockVirtualAllocation;
  # The virtual allocation starts with a DPH_ALLOCATION_HEADER structure
  o0AllocationHeader = fo0GetAllocationHeaderForVirtualAllocationAndPointerSize(
    oHeapBlockVirtualAllocation,
    oProcess.uPointerSize,
  );
  if not o0AllocationHeader:
    return None;
  oAllocationHeader = o0AllocationHeader;
  uPageHeapBlockStartAddress = oAllocationHeader.poAllocationInformation.fuGetValue();
  o0PageHeapBlock = fo0GetPageHeapBlockForProcessAndAddress(
    oProcess,
    uPageHeapBlockStartAddress,
  );
  if not o0PageHeapBlock:
    return None;
  oPageHeapBlock = o0PageHeapBlock;
  return cClass.fo0CreateHelper(
    uPointerSize = oProcess.uPointerSize,
    uPageHeapBlockStartAddress = uPageHeapBlockStartAddress,
    oPageHeapBlock = oPageHeapBlock,
    oHeapBlockVirtualAllocation = oHeapBlockVirtualAllocation,
    o0AllocationHeader = oAllocationHeader,
  );
