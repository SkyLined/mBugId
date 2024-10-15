from ..mHeapManager import cPageHeapManagerData;
from ..dxConfig import dxConfig;

def cProcess_fo0GetPageHeapManagerDataForAddressNearHeapBlock(oProcess, uAddressNearHeapBlock):
  if uAddressNearHeapBlock <= dxConfig["uMaxAddressOffset"]:
    return None; # Considered a NULL pointer;
  if uAddressNearHeapBlock >= (1 << ({"x86": 32, "x64": 64}[oProcess.sISA])):
    return None; # Value is not in the valid address range
  return cPageHeapManagerData.fo0GetForProcessAndAddressNearHeapBlock(
    oProcess,
    uAddressNearHeapBlock = uAddressNearHeapBlock,
  );
