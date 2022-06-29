from mWindowsAPI import cVirtualAllocation, fsHexNumber, oSystemInfo;

from .fo0GetAllocationHeaderForVirtualAllocationAndPointerSize import \
    fo0GetAllocationHeaderForVirtualAllocationAndPointerSize;
from .fo0GetPageHeapBlockForProcessAndAddress import \
    fo0GetPageHeapBlockForProcessAndAddress;
from .fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock import \
    fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock;
from .mPageHeapStructuresAndStaticValues import \
  DPH_BLOCK_INFORMATION32, DPH_BLOCK_INFORMATION64;

def cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock(
  cClass,
  oProcess,
  uAddressNearHeapBlock,
):
  if cClass.bDebugOutput: print(
    "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
    "Looking for page heap block related to address %s..." % (
      fsHexNumber(uAddressNearHeapBlock),
    ),
  );

  o0VirtualAllocationAtAddressNearHeapBlock = fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock(
    oProcess,
    uAddressNearHeapBlock,
    bDebugOutput = cClass.bDebugOutput,
  );
  if not o0VirtualAllocationAtAddressNearHeapBlock:
    if cClass.bDebugOutput: print(
      "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
      "No allocation near: %s\r\n  => No page heap manager data found" % (
        fsHexNumber(uAddressNearHeapBlock),
      ),
    );
    return None; # Cannot find any cirtual allocation near the address.
  oVirtualAllocationAtAddressNearHeapBlock = o0VirtualAllocationAtAddressNearHeapBlock;
  if oVirtualAllocationAtAddressNearHeapBlock.bReserved:
    # Let's assume this is an OOB read/write into a reserved allocation following a buffer.
    # We'll assume that this is only true if the offset is less than one page from the
    # start of the reserved allocation.
    iOffsetInReservedAllocation = oVirtualAllocationAtAddressNearHeapBlock.uStartAddress - uAddressNearHeapBlock;
    if iOffsetInReservedAllocation >= oSystemInfo.uPageSize:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "Reserved allocation contains %s at offset %s: %s\r\n  => No page heap manager data found" % (
          fsHexNumber(uAddressNearHeapBlock),
          fsHexNumber(iOffsetInReservedAllocation),
          oVirtualAllocationAtAddressNearHeapBlock,
        ),
      );
      return None;
    # In this case there should be a non-reserved allocation containing the buffer before
    # the reserved allocation. The address of the first byte before this reserved allocation
    # should be contained in this allocation and we can use that to look it up:
    uAddressInsidePotentialHeapBlockVirtualAllocation = oVirtualAllocationAtAddressNearHeapBlock.uStartAddress - 1;
    if cClass.bDebugOutput: print(
      "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
      "Looking for non-reserved allocation containing address %s" % (
        fsHexNumber(uAddressInsidePotentialHeapBlockVirtualAllocation),
      ),
    );
    o0VirtualAllocationAtAddressNearHeapBlock = fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock(
      oProcess,
      uAddressInsidePotentialHeapBlockVirtualAllocation,
      bDebugOutput = cClass.bDebugOutput,
    );
    if not o0VirtualAllocationAtAddressNearHeapBlock:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "No allocation contains %s\r\n  => No page heap manager data" % (
         fsHexNumber(uAddressInsidePotentialHeapBlockVirtualAllocation),
        ),
      );
      return None;
    oVirtualAllocationAtAddressNearHeapBlock = o0VirtualAllocationAtAddressNearHeapBlock;
    if o0VirtualAllocationAtAddressNearHeapBlock.bReserved:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "Found two reserved allocations near %s\r\n  => No page heap manager data" % (
         fsHexNumber(uAddressInsidePotentialHeapBlockVirtualAllocation),
        ),
      );
      return None;
  # At this point oVirtualAllocationAtAddressNearHeapBlock points to _allocated_ memory
  # let's see if it contains an allocation header:

  if cClass.bDebugOutput: print(
    "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
    "Looking for allocation header in allocation: %s" % (
      oVirtualAllocationAtAddressNearHeapBlock,
    ),
  );
  o0AllocationHeader = fo0GetAllocationHeaderForVirtualAllocationAndPointerSize(
    oVirtualAllocationAtAddressNearHeapBlock,
    oProcess.uPointerSize,
    bDebugOutput = cClass.bDebugOutput,
  );
  if o0AllocationHeader:
    oAllocationHeader = o0AllocationHeader;
    oAllocationHeaderVirtualAllocation = oVirtualAllocationAtAddressNearHeapBlock;
  else:
    if cClass.bDebugOutput: print(
      "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
      "No allocation header found in allocation %s" % (
        oVirtualAllocationAtAddressNearHeapBlock,
      ),
    );
    # If the heap block is over a certain size, page heap can allocate a separate
    # page for the allocation header right before the allocation for the heap block itself:
    uAddressInsidePotentialAllocationHeaderVirtualAllocation = oVirtualAllocationAtAddressNearHeapBlock.uStartAddress - 1;
    if cClass.bDebugOutput: print(
      "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
      "Looking for previous allocation containing address %s" % (
        fsHexNumber(uAddressInsidePotentialAllocationHeaderVirtualAllocation),
      ),
    );
    o0PotentialAllocationHeaderVirtualAllocation = fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock(
      oProcess,
      uAddressInsidePotentialAllocationHeaderVirtualAllocation,
      bDebugOutput = cClass.bDebugOutput,
    );
    if not o0PotentialAllocationHeaderVirtualAllocation:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "No previous allocation contains %s\r\n  => No page heap manager data found" % (
          fsHexNumber(uAddressInsidePotentialAllocationHeaderVirtualAllocation),
        ),
      );
      return None;
    oPotentialAllocationHeaderVirtualAllocation = o0PotentialAllocationHeaderVirtualAllocation;
    if oPotentialAllocationHeaderVirtualAllocation.bReserved:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "A reserved allocation covers %s: %s\r\n  => No page heap manager data" % (
          fsHexNumber(uAddressInsidePotentialAllocationHeaderVirtualAllocation),
          oPotentialAllocationHeaderVirtualAllocation,
        ),
      );
      return None;
    if oPotentialAllocationHeaderVirtualAllocation.uSize == oSystemInfo.uPageSize:
      # There is a single page-sized allocation before the allocation that we believe
      # contains the heap block. We believe this contains the allocation header.
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "The allocation header may be in a separate allocation at %s: %s" % (
          fsHexNumber(uAddressInsidePotentialAllocationHeaderVirtualAllocation),
          oPotentialAllocationHeaderVirtualAllocation,
        ),
      );
    elif (
      oPotentialAllocationHeaderVirtualAllocation.uEndAddress == oVirtualAllocationAtAddressNearHeapBlock.uEndAddress and
      oPotentialAllocationHeaderVirtualAllocation.uSize == oVirtualAllocationAtAddressNearHeapBlock.uSize + oSystemInfo.uPageSize
    ):
      # The allocation is one page larger than first reported and ends at the same
      # address. This new allocation potentially contains both allocation header
      # and the heap block:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "The allocation at %s is one page larger and contains the previously found allocation: %s" % (
          fsHexNumber(uAddressInsidePotentialAllocationHeaderVirtualAllocation),
          oPotentialAllocationHeaderVirtualAllocation,
        ),
      );
    else:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "The allocation at %s does not look like it contains an allocation header: %s\r\n  => No page heap manager data found" % (
          fsHexNumber(uAddressInsidePotentialAllocationHeaderVirtualAllocation),
          oPotentialAllocationHeaderVirtualAllocation,
        ),
      );
      return None;
    o0AllocationHeader = fo0GetAllocationHeaderForVirtualAllocationAndPointerSize(
      oPotentialAllocationHeaderVirtualAllocation,
      oProcess.uPointerSize,
      bDebugOutput = cClass.bDebugOutput,
    );
    if not o0AllocationHeader:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "No allocation header marker found in allocation %s either.\r\n => No page heap manager data" % (
          oPotentialAllocationHeaderVirtualAllocation,
        ),
      );
      return None;
    oAllocationHeader = o0AllocationHeader;
    oAllocationHeaderVirtualAllocation = oPotentialAllocationHeaderVirtualAllocation;
  # At this point we have found an allocation header. Let's try to find the
  # corresponding peag heap block: 
  if cClass.bDebugOutput: print(
    "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
    "Allocation header marker found in allocation %s" % (
      oAllocationHeaderVirtualAllocation,
    ),
  );
  uPageHeapBlockStartAddress = oAllocationHeader.poAllocationInformation.fuGetValue();
  o0PageHeapBlock = fo0GetPageHeapBlockForProcessAndAddress(
    oProcess,
    uPageHeapBlockStartAddress,
    bDebugOutput = cClass.bDebugOutput,
  );
  if not o0PageHeapBlock:
    if cClass.bDebugOutput: print(
      "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
      "page heap block not found at @ %s\r\n=> No page heap manager data" % (
        fsHexNumber(uPageHeapBlockStartAddress),
      )
    );
    return None;
  oPageHeapBlock = o0PageHeapBlock;
  uHeapBlockStartAddress = oPageHeapBlock.pUserAllocation.fuGetValue();
  uHeapBlockSize = oPageHeapBlock.nUserRequestedSize.fuGetValue();
  iOffsetBeforeStartOfHeapBlock = uHeapBlockStartAddress - uAddressNearHeapBlock;
  if iOffsetBeforeStartOfHeapBlock > 0:
    if iOffsetBeforeStartOfHeapBlock > oSystemInfo.uPageSize:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "address %s is %s bytes before [%s] heap block at @ %s\r\n=> No page heap manager data" % (
          fsHexNumber(uAddressNearHeapBlock),
          fsHexNumber(iOffsetBeforeStartOfHeapBlock),
          fsHexNumber(uHeapBlockSize),
          fsHexNumber(uHeapBlockStartAddress),
        )
      );
      return None;
    if cClass.bDebugOutput: print(
      "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
      "address %s is %s bytes before [%s] heap block at @ %s" % (
        fsHexNumber(uAddressNearHeapBlock),
        fsHexNumber(iOffsetBeforeStartOfHeapBlock),
        fsHexNumber(uHeapBlockSize),
        fsHexNumber(uHeapBlockStartAddress),
      )
    );
  else:
    uHeapBlockEndAddress = uHeapBlockStartAddress + uHeapBlockSize;
    iOffsetFromEndOfHeapBlock = uAddressNearHeapBlock - uHeapBlockEndAddress;
    if iOffsetFromEndOfHeapBlock > 0:
      if iOffsetFromEndOfHeapBlock > oSystemInfo.uPageSize:
        if cClass.bDebugOutput: print(
          "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
          "address %s is %s bytes after [%s] heap block at @ %s\r\n=> No page heap manager data" % (
            fsHexNumber(uAddressNearHeapBlock),
            fsHexNumber(iOffsetFromEndOfHeapBlock),
            fsHexNumber(uHeapBlockSize),
            fsHexNumber(uHeapBlockStartAddress),
          )
        );
        return None;
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "address %s is %s bytes after [%s] heap block at @ %s" % (
          fsHexNumber(uAddressNearHeapBlock),
          fsHexNumber(iOffsetFromEndOfHeapBlock),
          fsHexNumber(uHeapBlockSize),
          fsHexNumber(uHeapBlockStartAddress),
        )
      );
    else:
      if cClass.bDebugOutput: print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "address %s is at offset %s in [%s] heap block at @ %s" % (
          fsHexNumber(uAddressNearHeapBlock),
          fsHexNumber(-iOffsetBeforeStartOfHeapBlock),
          fsHexNumber(uHeapBlockSize),
          fsHexNumber(uHeapBlockStartAddress),
        )
      );

  oHeapBlockVirtualAllocation = cVirtualAllocation(
    oProcess.uId,
    oPageHeapBlock.pVirtualBlock.fuGetValue(),
  );
  # The page heap header structure at the start of the virtual allocation should point to a page heap allocation
  # information structure that points back to the same virtual allocation:
  DPH_BLOCK_INFORMATION = {4: DPH_BLOCK_INFORMATION32, 8: DPH_BLOCK_INFORMATION64}[oProcess.uPointerSize];
  bErrorsFound = False;
  uHeapBlockStartAddress = oPageHeapBlock.pUserAllocation.fuGetValue();
  uHeapBlockHeaderStartAddress = uHeapBlockStartAddress - DPH_BLOCK_INFORMATION.fuGetSize();
  uHeapBlockEndAddress = uHeapBlockStartAddress + oPageHeapBlock.nUserRequestedSize;
  if oPageHeapBlock.nVirtualBlockSize.fuGetValue() == 0:
    if cClass.bDebugOutput:
      print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "Page heap block reports virtual block size as 0."
      );
    bErrorsFound = True;
  if oPageHeapBlock.nVirtualAccessSize.fuGetValue() == 0:
    if cClass.bDebugOutput:
      print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "Page heap block reports virtual access size as 0."
      );
    bErrorsFound = True;
  if oPageHeapBlock.nUserRequestedSize.fuGetValue() == 0:
    if cClass.bDebugOutput:
      print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "Page heap block reports user requested size as 0."
      );
    bErrorsFound = True;
  if oPageHeapBlock.nUserActualSize.fuGetValue() == 0:
    if cClass.bDebugOutput:
      print(
        "cPageHeapManagerData_fo0GetForProcessAndAddressNearHeapBlock: " \
        "Page heap block reports user actual size as 0."
      );
    bErrorsFound = True;
  if bErrorsFound:
    if cClass.bDebugOutput:
      print("  => No valid page heap data found.");
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
    oProcess.uPointerSize,
    uPageHeapBlockStartAddress,
    oPageHeapBlock,
    oHeapBlockVirtualAllocation,
    oAllocationHeader,
    oAllocationHeaderVirtualAllocation,
    uHeapBlockHeaderStartAddress,
    o0PageHeapBlockHeader,
    u0HeapBlockEndPaddingSize,
  );

