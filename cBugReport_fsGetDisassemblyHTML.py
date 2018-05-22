import re;
from .dxConfig import dxConfig;

def fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sLine, bImportant = False):
  # If this line starts with an address and opcode, make those semi-transparent.
  oMatch = re.match(r"^([0-9a-fA-F`]+\s+)([0-9a-fA-F]+\s+)(.+)$", sLine);
  if oMatch:
    sAddress, sOpcode, sInstruction = oMatch.groups();
    return "".join([
      "<span class=\"DisassemblyAddress\">%s</span>" % oCdbWrapper.fsHTMLEncode(sAddress),
      "<span class=\"DisassemblyOpcode\">%s</span>" % oCdbWrapper.fsHTMLEncode(sOpcode),
      "<span class=\"DisassemblyInstruction%s\">%s</span>" % \
          (bImportant and " Important" or "", oCdbWrapper.fsHTMLEncode(sInstruction)),
    ]);
  return "<span class=\"DisassemblyInformation\">%s</span>" % oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8);
  
def cBugReport_fsGetDisassemblyHTML(oBugReport, oCdbWrapper, oProcess, uAddress, sDescriptionOfInstructionBeforeAddress = None, sDescriptionOfInstructionAtAddress = None):
  # See dxConfig.py for a description of these "magic" values.
  # In short, we need to guess how many bytes to disassemble to get the number of instructions we want disassembled.
  uDisassemblyBytesBefore = \
      dxConfig["uDisassemblyInstructionsBefore"] \
      * dxConfig["uDisassemblyAverageInstructionSize"] \
      + dxConfig["uDisassemblyAlignmentBytes"];
  uDisassemblyBytesAfter = \
      dxConfig["uDisassemblyInstructionsAfter"] \
      * dxConfig["uDisassemblyAverageInstructionSize"];
  oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uAddress);
  if not oVirtualAllocation.bAllocated:
    return None;
  # Get disassembly around code in which exception happened. This may not be possible if the instruction pointer points to unmapped memory.
  asDisassemblyBeforeAddressHTML = [];
  if uDisassemblyBytesBefore > 0:
    # Find out if we can get disassembly before uAddress by determining the start and end address we want and adjusting
    # them to the start and end address of the memory region.
    uStartAddress = max(uAddress - uDisassemblyBytesBefore, oVirtualAllocation.uStartAddress);
    uEndAddress = min(uAddress - 1, oVirtualAllocation.uEndAddress);
    if (uStartAddress < uEndAddress):
      asDisassemblyBeforeAddress = oProcess.fasExecuteCdbCommand(
        sCommand = "u 0x%X 0x%X;" % (uStartAddress, uEndAddress),
        sComment = "Disassemble up to address 0x%X" % uAddress,
        bOutputIsInformative = True,
        bRetryOnTruncatedOutput = True,
      );
    # Limit number of instructions
    asDisassemblyBeforeAddress = asDisassemblyBeforeAddress[-dxConfig["uDisassemblyInstructionsBefore"]:];
    if asDisassemblyBeforeAddress:
      # Optionally highlight and describe instruction before the address:
      if sDescriptionOfInstructionBeforeAddress:
        sInstructionBeforeAddress = asDisassemblyBeforeAddress.pop(-1);
      asDisassemblyBeforeAddressHTML = [
        fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sLine)
        for sLine in asDisassemblyBeforeAddress
      ];
      if sDescriptionOfInstructionBeforeAddress:
        asDisassemblyBeforeAddressHTML.append(
          "%s <span class=\"Important\">// %s</span>" % \
              (fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sInstructionBeforeAddress, bImportant = True), \
              sDescriptionOfInstructionBeforeAddress)
        );
  asDisassemblyAfterAddressHTML = [];
  if uDisassemblyBytesAfter > 0:
    # Find out if we can get disassembly after uAddress by determining the start and end address we want and adjusting
    # them to the start and end address of the memory region.
    uStartAddress = max(uAddress, oVirtualAllocation.uStartAddress);
    uEndAddress = min(uAddress + uDisassemblyBytesAfter, oVirtualAllocation.uEndAddress);
    if (uStartAddress < uEndAddress):
      asDisassemblyAtAndAfterAddress = oProcess.fasExecuteCdbCommand(
        sCommand = "u 0x%X 0x%X;" % (uStartAddress, uEndAddress),
        sComment = "Disassemble starting at address 0x%X" % uAddress, 
        bOutputIsInformative = True,
        bRetryOnTruncatedOutput = True,
      );
      if asDisassemblyAtAndAfterAddress:
        assert len(asDisassemblyAtAndAfterAddress) >= 2, \
            "Unexpected short disassembly output:\r\n%s" % "\r\n".join(asDisassemblyAtAndAfterAddress);
        # The first line contains the address of the instruction
        # disassembly starts with a line containing the address/symbol:
        sAddressLine = asDisassemblyAtAndAfterAddress.pop(0);
        sAddressLineHTML = fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sAddressLine);
        # First line of disassembly at address is important;
        sInstructionAtAddress = asDisassemblyAtAndAfterAddress.pop(0);
        sInstructionAtAddressHTML = fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sInstructionAtAddress, bImportant = True);
        if sDescriptionOfInstructionAtAddress:
          sInstructionAtAddressHTML += " <span class=\"Important\">// %s</span>" % sDescriptionOfInstructionAtAddress;
        # Limit the number of instructions, taking into account we already processed one:
        asDisassemblyAfterAddress = asDisassemblyAtAndAfterAddress[:dxConfig["uDisassemblyInstructionsAfter"] - 1];
        asDisassemblyAtAndAfterAddressHTML = [
          sAddressLineHTML,
          sInstructionAtAddressHTML,
        ] + [
          fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sLine)
          for sLing in asDisassemblyAfterAddress
        ];
  if not asDisassemblyBeforeAddressHTML:
    if not asDisassemblyAtAndAfterAddressHTML:
      return None;
    asDisassemblyBeforeAddressHTML = ["(prior disaeembly not possible)"];
  elif not asDisassemblyAtAndAfterAddressHTML:
    asDisassemblyAtAndAfterAddressHTML = ["(further disassembly not possible)"];
  return "<br/>\n".join(asDisassemblyBeforeAddressHTML + asDisassemblyAtAndAfterAddressHTML);
