from ..mHeapManager import cPageHeapManagerData;
from ..dxConfig import dxConfig;

def cProcess_fo0GetPageHeapManagerDataForPageHeapBlockStartAddress(oProcess, uPageHeapHeaderStartAddress):
  assert uPageHeapHeaderStartAddress > dxConfig["uMaxAddressOffset"], \
      "page heap header start address 0x%X is considered a NULL pointer" % uPageHeapHeaderStartAddress
  assert uPageHeapHeaderStartAddress < (1 << ({"x86": 32, "x64": 64}[oProcess.sISA])), \
      "page heap header start address 0x%X is invalid for %s ISA" % (uPageHeapHeaderStartAddress, oProcess.sISA);
  return cPageHeapManagerData.fo0GetForProcessAndPageHeapBlockStartAddress(oProcess, uPageHeapHeaderStartAddress);
