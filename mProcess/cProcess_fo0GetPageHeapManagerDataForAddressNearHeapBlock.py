from ..mHeapManager import cPageHeapManagerData;
from ..dxConfig import dxConfig;

def cProcess_fo0GetPageHeapManagerDataForAddressNearHeapBlock(oProcess, uAddressNearHeapBlock):
  if uAddressNearHeapBlock <= dxConfig["uMaxAddressOffset"]:
    return None; # Considered a NULL pointer;
  if uAddressNearHeapBlock >= (1 << ({"x86": 32, "x64": 64}[oProcess.sISA])):
    return None; # Value is not in the valid address range
  if oProcess.sISA == "x64" and uAddressNearHeapBlock >> 48 not in (0, 0xFFFF):
    # x64 supports 48 bits of address space for user and kernel mode
    # The upper 16 bits must be all 0 or all 1 for an address to be valid.
    return None;
  # TODO: In theory this should always work but it doesn't so I've added
  # an exception handler to work around it. I should find out when and why
  # it doesn't work and handle that correctly.
  try:
    return cPageHeapManagerData.fo0GetForProcessAndAddressNearHeapBlock(
      oProcess,
      uAddressNearHeapBlock = uAddressNearHeapBlock,
    );
  except OSError:
    return None;