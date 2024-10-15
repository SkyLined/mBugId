from mWindowsAPI import oSystemInfo;

from ..dxConfig import dxConfig;
from ..mCP437 import fsCP437HTMLFromBytesString;

from .fsGetHTMLForValue import fsGetHTMLForValue;
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
    asRegistersTableHTML.extend([
      '<tr>',
        '<td>', sRegisterName, '</td>',
        '<td> = </td>',
        '<td>', fsGetHTMLForValue(uRegisterValue, uBitSize), '</td>',
        '<td>', s0Details or "", '</td>',
      '</tr>\n',
    ]);
    if uRegisterValue < 1 << (oProcess.uPointerSize * 8):
      o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uRegisterValue);
      if o0VirtualAllocation and o0VirtualAllocation.bAllocated:
        oBugReport.fAddMemoryDump(
          uStartAddress = uRegisterValue - dxConfig["uRegisterPointerPreDumpSizeInPointers"] * oProcess.uPointerSizeInBytes,
          uEndAddress = uRegisterValue + dxConfig["uRegisterPointerPostDumpSizeInPointers"] * oProcess.uPointerSizeInBytes,
          asAddressDetailsHTML = ["%s = %s" % (sRegisterName, fsGetHTMLForValue(uRegisterValue, oProcess.uPointerSizeInBits))],
        );
      # Add memory remarks for anything that is not (close to) NULL.
      # Calculate the positive equivalent of the signed value for the register.
      uNegativeRegisterValue = {"x86": 1 << 32, "x64": 1 << 64}[oProcess.sISA] - uRegisterValue;
      if (
        uRegisterValue > oSystemInfo.uAllocationAddressGranularity
        and uNegativeRegisterValue > oSystemInfo.uAllocationAddressGranularity
      ):
        oBugReport.fAddMemoryRemark(
          "%s=%s" % (
            sRegisterName,
            fsGetHTMLForValue(uRegisterValue, oProcess.uPointerSizeInBits),
          ),
          uRegisterValue,
          None,
        );
  return sBlockHTMLTemplate % {
    "sName": "Registers",
    "sCollapsed": "Collapsed",
    "sContent": "<table class=\"Registers\">\n%s</table>" % "".join(asRegistersTableHTML),
  };

