from mWindowsSDK import PAGE_NOACCESS, PAGE_READWRITE;

from .fo0GetAllocationHeaderForVirtualAllocationAndPointerSize import \
    fo0GetAllocationHeaderForVirtualAllocationAndPointerSize;
from .fo0GetPageHeapBlockForProcessAndAddress import \
    fo0GetPageHeapBlockForProcessAndAddress;

gbDebugOutput = True;

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
    o0HeapBlockVirtualAllocation = oProcess.fo0GetVirtualAllocationForAddressNearHeapBlock(
      o0HeapBlockVirtualAllocation.uStartAddress - 1,
    );
    assert o0HeapBlockVirtualAllocation, \
        "Heap block at 0x%X`%X is 0x%X bytes, but there is no heap block before it!?" % (
          uAddressNearHeapBlock >> 32,
          uAddressNearHeapBlock & 0xFFFFFFFF,
        )
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
