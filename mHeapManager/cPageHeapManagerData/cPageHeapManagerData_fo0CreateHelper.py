from mWindowsSDK import PAGE_NOACCESS, PAGE_READWRITE;

from .mPageHeapStructuresAndStaticValues import \
  DPH_BLOCK_INFORMATION32, DPH_BLOCK_INFORMATION64;

gbDebugOutput = False;

def cPageHeapManagerData_fo0CreateHelper(
  cClass,
  uPointerSize,
  uPageHeapBlockStartAddress,
  oPageHeapBlock,
  oHeapBlockVirtualAllocation,
  o0AllocationHeader,
):
  # The page heap header structure at the start of the virtual allocation should point to a page heap allocation
  # information structure that points back to the same virtual allocation:
  DPH_BLOCK_INFORMATION = {4: DPH_BLOCK_INFORMATION32, 8: DPH_BLOCK_INFORMATION64}[uPointerSize];
  bErrorsFound = False;
  uHeapBlockStartAddress = oPageHeapBlock.pUserAllocation.fuGetValue();
  uHeapBlockHeaderStartAddress = uHeapBlockStartAddress - DPH_BLOCK_INFORMATION.fuGetSize();
  uHeapBlockEndAddress = uHeapBlockStartAddress + oPageHeapBlock.nUserRequestedSize;
  if not oHeapBlockVirtualAllocation.fbContainsAddress(uHeapBlockStartAddress):
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block reports heap block starts at 0x%X`%X, outside of virtual allocation." % (
        uHeapBlockStartAddress >> 32,
        uHeapBlockStartAddress & 0xFFFFFFFF)
      );
    bErrorsFound = True;
  if not oHeapBlockVirtualAllocation.fbContainsAddress(uHeapBlockHeaderStartAddress):
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block indicates page heap block header starts at 0x%X`%X, outside of virtual allocation." % (
        uHeapBlockHeaderStartAddress >> 32,
        uHeapBlockHeaderStartAddress & 0xFFFFFFFF)
      );
    bErrorsFound = True;
  if not oHeapBlockVirtualAllocation.fbContainsAddress(uHeapBlockEndAddress) and oHeapBlockVirtualAllocation.uEndAddress != uHeapBlockEndAddress:
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block reports heap block ends at 0x%X`%X, outside of virtual allocation." % (
        uHeapBlockEndAddress >> 32,
        uHeapBlockEndAddress & 0xFFFFFFFF)
      );
    bErrorsFound = True;
  uVirtualBlockAddress = oPageHeapBlock.pVirtualBlock.fuGetValue();
  if not oHeapBlockVirtualAllocation.fbContainsAddress(uVirtualBlockAddress):
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block reports virtual block at 0x%X`%X, outside of virtual allocation." % (
        uVirtualBlockAddress >> 32,
        uVirtualBlockAddress & 0xFFFFFFFF)
      );
    bErrorsFound = True;
  if oPageHeapBlock.nVirtualBlockSize.fuGetValue() == 0:
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block reports virtual block size as 0.");
    bErrorsFound = True;
  if oPageHeapBlock.nVirtualAccessSize.fuGetValue() == 0:
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block reports virtual access size as 0.");
    bErrorsFound = True;
  if oPageHeapBlock.nUserRequestedSize.fuGetValue() == 0:
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block reports user requested size as 0.");
    bErrorsFound = True;
  if oPageHeapBlock.nUserActualSize.fuGetValue() == 0:
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper WARNING: Page heap block reports user actual size as 0.");
    bErrorsFound = True;
  if bErrorsFound:
    if gbDebugOutput:
      print("cPageHeapManagerData_fo0CreateHelper: Virtual allocation at 0x%X`%X-0x%X`%X." % (
        oHeapBlockVirtualAllocation.uStartAddress >> 32,
        oHeapBlockVirtualAllocation.uStartAddress & 0xFFFFFFFF,
        oHeapBlockVirtualAllocation.uEndAddress >> 32,
        oHeapBlockVirtualAllocation.uEndAddress & 0xFFFFFFFF,
      ));
      print("cPageHeapManagerData_fo0CreateHelper: Page heap block at 0x%X`%X:" % (
        uPageHeapBlockStartAddress >> 32,
        uPageHeapBlockStartAddress & 0xFFFFFFFF,
      ));
      print("\r\n".join("cPageHeapManagerData_fo0CreateHelper: %s" % s for s in oPageHeapBlock.fasDump()));
      print("\r\n".join("cPageHeapManagerData_fo0CreateHelper: %s" % s for s in oHeapBlockVirtualAllocation.fasDumpContents(
        uStartOffset = min(
          0,
          max(
            uPageHeapBlockStartAddress,
            oHeapBlockVirtualAllocation.uEndAddress - 0x200,
          ) - oHeapBlockVirtualAllocation.uStartAddress,
        ),
        u0Size = 0x200,
        uWordSize = uPointerSize,
      )));
      print("cPageHeapManagerData_fo0CreateHelper: no page heap data found.");
    return None;
        
  if oHeapBlockVirtualAllocation.bAllocated:
    # A DPH_BLOCK_INFORMATION structure is stored immediately before the heap block in the same allocation.
    o0PageHeapBlockHeader = oHeapBlockVirtualAllocation.foReadStructureForOffset(
      DPH_BLOCK_INFORMATION,
      uHeapBlockHeaderStartAddress - oHeapBlockVirtualAllocation.uStartAddress,
    );
    u0HeapBlockEndPaddingSize = oHeapBlockVirtualAllocation.uEndAddress - uHeapBlockEndAddress;
  else:
    u0HeapBlockEndPaddingSize = None;
  return cClass(
    uPointerSize,
    uPageHeapBlockStartAddress,
    oPageHeapBlock,
    oHeapBlockVirtualAllocation,
    o0AllocationHeader,
    uHeapBlockHeaderStartAddress,
    o0PageHeapBlockHeader,
    u0HeapBlockEndPaddingSize,
  );

