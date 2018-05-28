import re;
from .dxConfig import dxConfig;

def fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sLine, bHighlightLine, sRemark):
  # If this line starts with an address and opcode, make those semi-transparent.
  oMatch = re.match(r"^([0-9a-fA-F`]+\s+)([0-9a-fA-F]+\s+)(.+)$", sLine);
  if oMatch:
    sAddress, sOpcode, sInstruction = oMatch.groups();
    return "<tr>%s</tr>" % "".join([
      "<td class=\"DisassemblyAddress%s\">%s</td>" % (bHighlightLine and " Important" or "", oCdbWrapper.fsHTMLEncode(sAddress)),
      "<td class=\"DisassemblyOpcode%s\">%s</td>" % (bHighlightLine and " Important" or "", oCdbWrapper.fsHTMLEncode(sOpcode)),
      "<td class=\"DisassemblyInstruction%s\">%s%s</td>" % (
        bHighlightLine and " Important" or "",
        oCdbWrapper.fsHTMLEncode(sInstruction),
        sRemark and (
          bHighlightLine and (" // %s" % sRemark) or (" <span class=\"Important\">// %s</span>" % sRemark)
        ) or "",
      ),
    ]);
  return "<tr><td colspan=\"3\" class=\"DisassemblyInformation%s\">%s</td></tr>" % \
      (bHighlightLine and " Important" or "", oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
  
def cBugReport_fsGetDisassemblyHTML(oBugReport, oCdbWrapper, oProcess, uAddress, sDescriptionOfInstructionBeforeAddress = None, sDescriptionOfInstructionAtAddress = None):
  # See dxConfig.py for a description of these "magic" values.
  # In short, we need to guess how many bytes to disassemble to get the number of instructions we want disassembled.
  uDisassemblyBytesBefore = \
      dxConfig["uDisassemblyInstructionsBefore"] \
      * dxConfig["uDisassemblyAverageInstructionSize"] \
      + dxConfig["uDisassemblyAlignmentBytes"];
  oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uAddress);
  if not oVirtualAllocation.bAllocated:
    return None;
  # Get disassembly around code in which exception happened. This may not be possible if the instruction pointer points to unmapped memory.
  asDisassemblyBeforeAddressHTML = [];
  srIgnoredMemoryAccessError = r"^\s*\^ Memory access error in '.+'$";
  if uDisassemblyBytesBefore > 0:
    # Find out if we can get disassembly before uAddress by determining the start and end address we want and adjusting
    # them to the start and end address of the memory region.
    uStartAddress = max(uAddress - uDisassemblyBytesBefore, oVirtualAllocation.uStartAddress);
    uLastAddress = min(uAddress, oVirtualAllocation.uEndAddress) - 1;
    if (uStartAddress < uLastAddress):
      asDisassemblyBeforeAddress = oProcess.fasExecuteCdbCommand(
        sCommand = "u 0x%X 0x%X;" % (uStartAddress, uLastAddress),
        sComment = "Disassemble up to address 0x%X" % uAddress,
        bOutputIsInformative = True,
        bRetryOnTruncatedOutput = True,
        srIgnoredErrors = srIgnoredMemoryAccessError,
      );
      if re.match(srIgnoredMemoryAccessError, asDisassemblyBeforeAddress[-1]):
        # If the virtual memory allocation ends shortly after the address, we could see this error:
        asDisassemblyBeforeAddress.pop();
      assert len(asDisassemblyBeforeAddress) >= 2, \
          "Unexpectedly short disassembly output:\r\n%s" % "\r\n".join(asDisassemblyBeforeAddress);
      # Limit number of instructions
      asDisassemblyBeforeAddress = asDisassemblyBeforeAddress[-dxConfig["uDisassemblyInstructionsBefore"]:];
      if asDisassemblyBeforeAddress:
        # Optionally highlight and describe instruction before the address:
        asDisassemblyBeforeAddressHTML = [
          fsHTMLEncodeAndColorDisassemblyLine(
            oCdbWrapper = oCdbWrapper,
            sLine = asDisassemblyBeforeAddress[uIndex],
            bHighlightLine = False,
            sRemark = uIndex == len(asDisassemblyBeforeAddress) - 1 and sDescriptionOfInstructionBeforeAddress or None,
          )
          for uIndex in xrange(len(asDisassemblyBeforeAddress))
        ];
  asDisassemblyAfterAddressHTML = [];
  if dxConfig["uDisassemblyInstructionsAfter"] > 0:
    # Get disassembly after uAddress is easier, as we can just as for oVirtualAllocation.uEndAddress instructions
    asDisassemblyAtAndAfterAddress = oProcess.fasExecuteCdbCommand(
      sCommand = "u 0x%X L%d;" % (uAddress, dxConfig["uDisassemblyInstructionsAfter"]),
      sComment = "Disassemble starting at address 0x%X" % uAddress, 
      bOutputIsInformative = True,
      bRetryOnTruncatedOutput = True,
      srIgnoredErrors = srIgnoredMemoryAccessError,
    );
    assert len(asDisassemblyAtAndAfterAddress) >= 2, \
        "Unexpectedly short disassembly output:\r\n%s" % "\r\n".join(asDisassemblyAtAndAfterAddress);
    # The first line copntains the symbol at the address where we started disassembly, which we do not want in the
    # output:
    asDisassemblyAtAndAfterAddress.pop(0);
    if re.match(srIgnoredMemoryAccessError, asDisassemblyAtAndAfterAddress[-1]):
      # If the virtual memory allocation ends shortly after the address, we could an error that we want to remove:
      asDisassemblyAtAndAfterAddress.pop();
    asDisassemblyAtAndAfterAddressHTML = [
      fsHTMLEncodeAndColorDisassemblyLine(
        oCdbWrapper = oCdbWrapper,
        sLine = asDisassemblyAtAndAfterAddress[uIndex],
        bHighlightLine = uIndex == 0,
        sRemark = uIndex == 0 and sDescriptionOfInstructionAtAddress or None,
      )
      for uIndex in xrange(len(asDisassemblyAtAndAfterAddress))
    ];
  if not asDisassemblyBeforeAddressHTML:
    if not asDisassemblyAtAndAfterAddressHTML:
      return None;
    asDisassemblyBeforeAddressHTML = ["(prior disassembly not possible)"];
  elif not asDisassemblyAtAndAfterAddressHTML:
    asDisassemblyAtAndAfterAddressHTML = ["(further disassembly not possible)"];
  return "<table>%s</table>" % "\n".join(asDisassemblyBeforeAddressHTML + asDisassemblyAtAndAfterAddressHTML);
