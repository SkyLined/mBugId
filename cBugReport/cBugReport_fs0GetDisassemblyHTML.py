import re;

from mWindowsAPI import fsHexNumber;

from ..dxConfig import dxConfig;

grbAddressOpCodeInstruction = re.compile(
  rb"\A"
  rb"([0-9a-fA-F`]+\s+)"
  rb"([0-9a-fA-F]+\s+)"
  rb"(.+)"
  rb"\Z"
);

def fsHTMLEncodeAndColorDisassemblyInstruction(oInstruction, bHighlightLine, s0Remark):
  # If this line starts with an address and opcode, make those semi-transparent.
  return "<tr>%s</tr>" % "".join([
    "<td class=\"DisassemblyColumn DisassemblyAddress%s\">%s</td>" % (
      " Important" if bHighlightLine else "",
      "%X" % oInstruction.uAddress,
    ),
    "<td class=\"DisassemblyColumn DisassemblyOpcode%s\">%s</td>" % (
      " Important" if bHighlightLine else "",
      oInstruction.sBytes,
    ),
    "<td class=\"DisassemblyColumn DisassemblyInstructionName%s\">%s</td>" % (
      " Important" if bHighlightLine else "",
      oInstruction.sName,
    ),
    "<td class=\"DisassemblyColumn DisassemblyInstructionArguments%s\">%s</td>" % (
      " Important" if bHighlightLine else "",
      oInstruction.sArguments,
    ),
    "<td class=\"DisassemblyColumn DisassemblyInstructionRemark%s\">%s</td>" % (
      " Important" if (bHighlightLine or s0Remark is not None) else "",
      " // %s" % s0Remark if s0Remark is not None else "",
    ),
  ]);
  
def cBugReport_fs0GetDisassemblyHTML(
    oBugReport,
    oProcess,
    uAddress,
    s0DescriptionOfInstructionBeforeAddress = None,
    s0DescriptionOfInstructionAtAddress = None,
  ):
  # See dxConfig.py for a description of these "magic" values.
  # In short, we need to guess how many bytes to disassemble to get the number of instructions we want disassembled.
  uDisassemblyBytesBefore = \
      dxConfig["uDisassemblyInstructionsBefore"] \
      * dxConfig["uDisassemblyAverageInstructionSize"] \
      + dxConfig["uDisassemblyAlignmentBytes"];
  o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uAddress);
  if not o0VirtualAllocation or not o0VirtualAllocation.bAllocated:
    return None;
  # Get disassembly around code in which exception happened. This may not be possible if the instruction pointer points to unmapped memory.
  asDisassemblyBeforeAddressHTML = [];
  if uDisassemblyBytesBefore > 0:
    # Find out if we can get disassembly before uAddress by determining the start and end address we want and adjusting
    # them to the start and end address of the memory region.
    uStartAddress = max(uAddress - uDisassemblyBytesBefore, o0VirtualAllocation.uStartAddress);
    uLastAddress = min(uAddress, o0VirtualAllocation.uEndAddress) - 1;
    if (uStartAddress < uLastAddress):
      o0DisassemblyBeforeAddress = oProcess.fo0GetDisassemblyForStartAddressAndNumberOfBytes(
        uStartAddress = uStartAddress,
        uNumberOfBytes = uLastAddress - uStartAddress,
      );
      assert o0DisassemblyBeforeAddress is not None, \
          "Cannot diassemble at address %s" % fsHexNumber(uStartAddress);
      assert len(o0DisassemblyBeforeAddress) >= 2, \
          "Unexpectedly short disassembly output at address %s:\r\n%s" % (
            fsHexNumber(uStartAddress),
            o0DisassemblyBeforeAddress,
          );
      uStartIndex = max(0, len(o0DisassemblyBeforeAddress) - dxConfig["uDisassemblyInstructionsBefore"]);
      if uStartIndex < len(o0DisassemblyBeforeAddress):
        # Optionally highlight and describe instruction before the address:
        asDisassemblyBeforeAddressHTML = [
          fsHTMLEncodeAndColorDisassemblyInstruction(
            oInstruction = o0DisassemblyBeforeAddress.foGetInstruction(uIndex),
            bHighlightLine = False,
            s0Remark = s0DescriptionOfInstructionBeforeAddress if (
              s0DescriptionOfInstructionBeforeAddress is not None
              and uIndex == len(o0DisassemblyBeforeAddress) - 1
            ) else None,
          )
          for uIndex in range(uStartIndex, len(o0DisassemblyBeforeAddress))
        ];
  asDisassemblyAtAndAfterAddressHTML = [];
  if dxConfig["uDisassemblyInstructionsAfter"] > 0:
    # Get disassembly after uAddress is easier, as we can just as for o0VirtualAllocation.uEndAddress instructions
    o0DisassemblyAtAndAfterAddress = oProcess.fo0GetDisassemblyForStartAddressAndNumberOfInstructions(
      uStartAddress = uAddress,
      uNumberOfInstructions = dxConfig["uDisassemblyInstructionsAfter"],
    );
    assert o0DisassemblyAtAndAfterAddress is not None, \
        "Cannot diassemble at address %s" % fsHexNumber(uAddress);
    # The first line contains the symbol at the address where we started disassembly, which we do not want in the
    # output:
    asDisassemblyAtAndAfterAddressHTML = [
      fsHTMLEncodeAndColorDisassemblyInstruction(
        oInstruction = o0DisassemblyAtAndAfterAddress.foGetInstruction(uIndex),
        bHighlightLine = uIndex == 0,
        s0Remark = s0DescriptionOfInstructionAtAddress if (
          s0DescriptionOfInstructionAtAddress is not None 
          and uIndex == 0
       ) else None,
      )
      for uIndex in range(len(o0DisassemblyAtAndAfterAddress))
    ];
  if not asDisassemblyBeforeAddressHTML:
    if not asDisassemblyAtAndAfterAddressHTML:
      return None;
    asDisassemblyBeforeAddressHTML = ["(prior disassembly not possible)"];
  elif not asDisassemblyAtAndAfterAddressHTML:
    asDisassemblyAtAndAfterAddressHTML = ["(further disassembly not possible)"];
  return "<table>%s</table>" % "\n".join(asDisassemblyBeforeAddressHTML + asDisassemblyAtAndAfterAddressHTML);
