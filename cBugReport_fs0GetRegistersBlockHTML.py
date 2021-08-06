from .dxConfig import dxConfig;

gdaxbRelevantRegisters_by_sISA = {
  #  NAME    SIZE   SYMBOL
  "x86": [
    [b"eax",    8,  True],
    [b"ebx",    8,  True],
    [b"ecx",    8,  True],
    [b"edx",    8,  True],
    [b"esi",    8,  True],
    [b"edi",    8,  True],
    [b"esp",    8,  True],
    [b"ebp",    8,  True],
    [b"xmm0",   32, False],
    [b"xmm1",   32, False],
    [b"xmm2",   32, False],
    [b"xmm3",   32, False],
    [b"xmm4",   32, False],
    [b"xmm5",   32, False],
    [b"xmm6",   32, False],
    [b"xmm7",   32, False],
  ],
  "x64": [
    [b"rax",    16, True],
    [b"rbx",    16, True],
    [b"rcx",    16, True],
    [b"rdx",    16, True],
    [b"rsi",    16, True],
    [b"rdi",    16, True],
    [b"rsp",    16, True],
    [b"rbp",    16, True],
    [b"r8",     16, True],
    [b"r9",     16, True],
    [b"r10",    16, True],
    [b"r11",    16, True],
    [b"r12",    16, True],
    [b"r13",    16, True],
    [b"r14",    16, True],
    [b"r15",    16, True],
    [b"xmm0",   16, False],
    [b"xmm1",   16, False],
    [b"xmm2",   16, False],
    [b"xmm3",   16, False],
    [b"xmm4",   16, False],
    [b"xmm5",   16, False],
    [b"xmm6",   16, False],
    [b"xmm7",   16, False],
    [b"xmm8",   16, False],
    [b"xmm9",   16, False],
    [b"xmm10",  16, False],
    [b"xmm11",  16, False],
    [b"xmm12",  16, False],
    [b"xmm13",  16, False],
    [b"xmm14",  16, False],
    [b"xmm15",  16, False],
  ],
}

def cBugReport_fs0GetRegistersBlockHTML(oBugReport, oProcess, oWindowsAPIThread):
  # Create and add registers block
  d0uRegisterValue_by_sbName = oWindowsAPIThread.fd0uGetRegisterValueByName();
  if d0uRegisterValue_by_sbName is None:
    return None;
  duRegisterValue_by_sbName = d0uRegisterValue_by_sbName;
  asRegistersTableHTML = [];
  for (sbRegisterName, uPadding, bShowSymbol) in gdaxbRelevantRegisters_by_sISA[oProcess.sISA]:
    sRegisterName = str(sbRegisterName, "ascii", "strict");
    uRegisterValue = duRegisterValue_by_sbName[sbRegisterName];
    sRegisterValue = "%X" % uRegisterValue;
    sValuePadding = "0" * (uPadding - len(sRegisterValue));
    sb0Symbol = oProcess.fsb0GetSymbolForAddress(uRegisterValue) if bShowSymbol else None;
    asRegistersTableHTML.extend([
      '<tr>',
        '<td>', sRegisterName, '</td>',
        '<td> = </td>',
        '<td><span class="HexNumberHeader">0x', sValuePadding, '</span>', sRegisterValue, '</td>',
        '<td>', str(sb0Symbol, "ascii", "strict") if sb0Symbol else "", '</td>',
      '</tr>\n',
    ]);
    if oProcess.foGetVirtualAllocationForAddress(uRegisterValue).bAllocated:
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

from .sBlockHTMLTemplate import sBlockHTMLTemplate;
