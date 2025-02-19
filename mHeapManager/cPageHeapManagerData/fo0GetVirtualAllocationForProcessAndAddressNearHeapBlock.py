from mWindowsAPI import cVirtualAllocation, fsHexNumber;

from ...dxConfig import dxConfig;

def fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock(oProcess, uAddressNearHeapBlock, bDebugOutput = False):
  if uAddressNearHeapBlock < dxConfig["uMaxAddressOffset"]:
    if bDebugOutput: print(
      "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
          "no virtual allocation for NULL pointer %s\r\n  => No virtual allocation found" % (
        fsHexNumber(uAddressNearHeapBlock),
      ),
    );
    return None; # quick return for NULL pointers
  if uAddressNearHeapBlock >= (1 << ({"x86": 32, "x64": 64}[oProcess.sISA])):
    if bDebugOutput: print(
      "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
          "no virtual allocation for invalid pointer value %s\r\n  => No virtual allocation found" % (
        fsHexNumber(uAddressNearHeapBlock),
      ),
    );
    return None; # quick return for invalid addresses.
  # Page heap reserves a memory page immediately after each heap block as a guard page.
  # This triggers an access violation when code attempts to access memory out-of-bounds
  # beyond the end of the heap block.
  # Page heap keeps freed heap blocks allocated but inaccessible or reserved for some time.
  # This triggers an access violation when code attempts to access memory after freeing
  # it.
  # If still allocated, the memory page that contains the (freed) heap block contains
  # useful information stored by page heap.
  
  # We will try to find that allocated memory page containing page heap information.
  # The address passed as an argument may point inside it in case of a use-after-free:
  # in that case the memory at uAddress should be allocated but inaccessible. It may also
  # point inside it in case of an attempt to access memory partially out-of-bounds across
  # a page boundary. It may point to a reserved page immediately after the allocated
  # memory page we want in case of an out-of-bounds memory access.

  # Let's see if the virtual allocation at uAddress is valid (required), not free (required)
  # and not executable (heap memory is never executable)
  if bDebugOutput: print(
    "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
        "Getting virtual allocation at %s" % (
      fsHexNumber(uAddressNearHeapBlock),
    )
  );
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, uAddressNearHeapBlock);
  if not oVirtualAllocation.bIsValid or oVirtualAllocation.bFree:
    if bDebugOutput: print(
      "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
          "Virtual allocation at %s is %s\r\n  => None" % (
        fsHexNumber(uAddressNearHeapBlock),
        "not valid" if not oVirtualAllocation.bIsValid else
            "free",
      )
    );
    return None;
  # If we request a virtual allocation somewhere in the middle of a reserved area,
  # we will get one that starts on the page of the address we specified, not the
  # start of the reserved area. So, in this case we will try the page before and
  # see if we get a reserved virtual allocation with the same end address. By
  # repeating this as often as possible, we can find the start of the reserved area
  # and return a virtual allocation that covers it completely.
  bAllocationExpanded = False;
  if oVirtualAllocation.bReserved:
    uAddressInPageBeforeCurrentVirtualAllocation = oVirtualAllocation.uStartAddress - 1;
    if bDebugOutput: print(
      "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
          "Getting virtual allocation at %s" % (
        fsHexNumber(uAddressInPageBeforeCurrentVirtualAllocation),
      )
    );
    oVirtualAllocationBeforeCurrentVirtualAllocation = cVirtualAllocation(oProcess.uId, uAddressInPageBeforeCurrentVirtualAllocation);
    if (
      oVirtualAllocationBeforeCurrentVirtualAllocation.bReserved
      and oVirtualAllocationBeforeCurrentVirtualAllocation.uEndAddress == oVirtualAllocation.uEndAddress
    ):
      oVirtualAllocation = oVirtualAllocationBeforeCurrentVirtualAllocation;
      bAllocationExpanded = True;
      if bDebugOutput: print(
        "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
            "Virtual allocation expanded"
      );
  if bAllocationExpanded and bDebugOutput: print(
    "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
        "reserved virtual allocation was expanded: %s" % (
      oVirtualAllocation,
    ),
  );
  if bDebugOutput: print(
    "cPageHeapManagerData fo0GetVirtualAllocationForProcessAndAddressNearHeapBlock: " \
        "Virtual allocation at %s\r\n  => %s" % (
    fsHexNumber(uAddressNearHeapBlock),
    oVirtualAllocation,
  ));
  return oVirtualAllocation;
