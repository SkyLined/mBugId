from ..dxConfig import dxConfig;
from ..mCP437 import fsCP437HTMLFromBytesString;

from .sBlockHTMLTemplate import sBlockHTMLTemplate;

def cBugReport_fs0GetRegistersBlockHTML(oBugReport, oProcess, oWindowsAPIThread):
  # Create and add registers block
  a0txRegisters = oProcess.fa0txGetRegistersForThreadId(oWindowsAPIThread.uId);
  if a0txRegisters is None:
    return None;
  atxRegisters = a0txRegisters;
  asRegistersTableHTML = [];
  for (sbRegisterName, uRegisterValue, uBitSize, s0Details) in atxRegisters:
    sRegisterName = fsCP437HTMLFromBytesString(sbRegisterName);
    sRegisterValue = "%X" % uRegisterValue;
    sValuePadding = "0" * ((uBitSize >> 2) - len(sRegisterValue));
    asRegistersTableHTML.extend([
      '<tr>',
        '<td>', sRegisterName, '</td>',
        '<td> = </td>',
        '<td><span class="HexNumberHeader">0x', sValuePadding, '</span>', sRegisterValue, '</td>',
        '<td>', s0Details or "", '</td>',
      '</tr>\n',
    ]);
    if uRegisterValue < 1 << (oProcess.uPointerSize * 8):
      o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uRegisterValue);
      if o0VirtualAllocation and o0VirtualAllocation.bAllocated:
        uStartAddress = uRegisterValue;
        uEndAddress = uStartAddress + dxConfig["uRegisterPointerDumpSizeInPointers"];
        sDescription = "Pointed to by register %s" % sRegisterName;
        oBugReport.fAddMemoryDump(uStartAddress, uEndAddress, sDescription);
        oBugReport.atxMemoryRemarks.append(("Register %s" % sRegisterName, uRegisterValue, None));
  return sBlockHTMLTemplate % {
    "sName": "Registers",
    "sCollapsed": "Collapsed",
    "sContent": "<table class=\"Registers\">\n%s</table>" % "".join(asRegistersTableHTML),
  };

