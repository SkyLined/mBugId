from mWindowsAPI import cVirtualAllocation;

from ..dxConfig import dxConfig;

gbDebugOutput = True;

def cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock(oProcess, uAddressNearHeapBlock):
  if uAddressNearHeapBlock < dxConfig["uMaxAddressOffset"]:
    if gbDebugOutput: print("cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock: no virtual allocation for NULL pointer 0x%X`%X\r\n=> None" % (
      uAddressNearHeapBlock >> 32,
      uAddressNearHeapBlock & 0xFFFFFFFF,
    ));
    return None; # quick return for NULL pointers
  if uAddressNearHeapBlock >= (1 << ({"x86": 32, "x64": 64}[oProcess.sISA])):
    if gbDebugOutput: print("cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock: no virtual allocation for invalid pointer value 0x%X`%X\r\n=> None" % (
      uAddressNearHeapBlock >> 32,
      uAddressNearHeapBlock & 0xFFFFFFFF,
    ));
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
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, uAddressNearHeapBlock);
  if not oVirtualAllocation.bIsValid or oVirtualAllocation.bFree:
    if gbDebugOutput: print("cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock: Virtual allocation at 0x%X`%X is %s\r\n=> None" % (
      uAddressNearHeapBlock >> 32,
      uAddressNearHeapBlock & 0xFFFFFFFF,
      "not valid" if not oVirtualAllocation.bIsValid else
          "free",
    ));
    return None;
  if gbDebugOutput: print("cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock: Virtual allocation at 0x%X`%X\r\n=> %s" % (
    uAddressNearHeapBlock >> 32,
    uAddressNearHeapBlock & 0xFFFFFFFF,
    oVirtualAllocation,
  ));
  if oVirtualAllocation.bAllocated:
    return oVirtualAllocation;
  assert oVirtualAllocation.bReserved, \
      "Not allocated, free or reserved? %s" % oVirtualAllocation;
  # If the virtual allocation at uAddressNearHeapBlock is reserved, we may be dealing with an out-of-bounds
  # access in a guard page. Let's assume we won't be out-of-bounds by more than a page:
  if uAddressNearHeapBlock >= oVirtualAllocation.uStartAddress + oVirtualAllocation.uPageSize:
    if gbDebugOutput: print("cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock: Virtual allocation at 0x%X`%X is reserved and starts 0x%X bytes before\r\n=> None" % (
      uAddressNearHeapBlock >> 32,
      uAddressNearHeapBlock & 0xFFFFFFFF,
      uAddressNearHeapBlock - oVirtualAllocation.uStartAddress,
    ));
    return None;
  # Let's look at the virtual allocation right before it:
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, oVirtualAllocation.uStartAddress - 1);
  # This must be allocated and not executable:
  if not oVirtualAllocation.bIsValid or not oVirtualAllocation.bAllocated:
    if gbDebugOutput: print(
      "cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock: Virtual allocation at 0x%X`%X is reserved and the previous allocation is %s\r\n=> None" % (
      uAddressNearHeapBlock >> 32,
      uAddressNearHeapBlock & 0xFFFFFFFF,
      "not valid" if not oVirtualAllocation.bIsValid else
          "not allocated",
    ));
    return None;
  if gbDebugOutput: print("cProcess_fo0GetVirtualAllocationForAddressNearHeapBlock: Virtual allocation before 0x%X`%X\r\n=> %s" % (
    uAddressNearHeapBlock >> 32,
    uAddressNearHeapBlock & 0xFFFFFFFF,
    oVirtualAllocation,
  ));
  return oVirtualAllocation;
