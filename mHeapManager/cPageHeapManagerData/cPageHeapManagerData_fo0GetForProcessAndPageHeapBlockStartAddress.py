from mWindowsAPI import cVirtualAllocation;
from mWindowsSDK import PAGE_NOACCESS, PAGE_READWRITE;

from .fo0GetAllocationHeaderForVirtualAllocationAndPointerSize import \
  fo0GetAllocationHeaderForVirtualAllocationAndPointerSize;
from .fo0GetPageHeapBlockForProcessAndAddress import \
  fo0GetPageHeapBlockForProcessAndAddress;

gbDebugOutput = False;

def cPageHeapManagerData_fo0GetForProcessAndPageHeapBlockStartAddress(cClass, oProcess, uPageHeapBlockStartAddress):
  o0PageHeapBlock = fo0GetPageHeapBlockForProcessAndAddress(
    oProcess,
    uPageHeapBlockStartAddress,
  );
  if not o0PageHeapBlock:
    return None;
  oPageHeapBlock = o0PageHeapBlock;
  oHeapBlockVirtualAllocation = cVirtualAllocation(
    uProcessId = oProcess.uId,
    uAddress = oPageHeapBlock.pVirtualBlock.fuGetValue(),
  );
  if not oHeapBlockVirtualAllocation.bAllocated:
    if gbDebugOutput:
      print("cPageHeapManagerData: no virtual memory allocated for heap block at 0x%X`%X" %(
        oPageHeapBlock.pVirtualBlock >> 32,
        oPageHeapBlock.pVirtualBlock & 0xFFFFFFFF,
      ));
    return None;
  o0AllocationHeader = fo0GetAllocationHeaderForVirtualAllocationAndPointerSize(
    oHeapBlockVirtualAllocation,
    oProcess.uPointerSize,
  );
  return cClass.fo0CreateHelper(
    uPointerSize = oProcess.uPointerSize,
    uPageHeapBlockStartAddress = uPageHeapBlockStartAddress,
    oPageHeapBlock = oPageHeapBlock,
    oHeapBlockVirtualAllocation = oHeapBlockVirtualAllocation,
    o0AllocationHeader = o0AllocationHeader,
  );
