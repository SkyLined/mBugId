import re;
from dxConfig import dxConfig;

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
  uDisassemblyBytesBefore = \
      dxConfig["uDisassemblyInstructionsBefore"] \
      * dxConfig["uDisassemblyAverageInstructionSize"] \
      + dxConfig["uDisassemblyAlignmentBytes"];
  uDisassemblyBytesAfter = \
      dxConfig["uDisassemblyInstructionsAfter"] \
      * dxConfig["uDisassemblyAverageInstructionSize"];
  # Get disassembly around code in which exception happened. This may not be possible if the instruction pointer points to unmapped memory.
  asHTML = [];
  if uDisassemblyBytesBefore > 0:
    while uDisassemblyBytesBefore > 0:
      # Get disassembly before address
      uStartAddress = uAddress - uDisassemblyBytesBefore;
      uEndAddress = uAddress - 1;
      # Note: cannot use "u {start address} L{length}" as length is number of instructions, and we want number of bytes
      # so we use "u {start address} {end address}". Also, the start and end may not be in a valid memory region, so we
      # have to check before attempting to disassemble, or we may get an error. If either the start or end is in an
      # invalid region, no disassmbly is returned. In this case we move the START address closer to the end address, as
      # the later is more likely to be correct. We will try again and again, until we find that we cannot disassmble
      # anything.
      asDisassemblyBeforeAddress = oProcess.fasExecuteCdbCommand(
        sCommand = ".if ($vvalid(0x%X, 1)) { .if ($vvalid(0x%X, 1)) { u 0x%X 0x%X; } };" % \
            (uStartAddress, uEndAddress, uStartAddress, uEndAddress),
        sComment = "Disassemble up to address 0x%X" % uAddress,
        bOutputIsInformative = True,
        bRetryOnTruncatedOutput = True,
      );
      if len(asDisassemblyBeforeAddress) > 0:
        break;
      uDisassemblyBytesBefore -= 1;
    # Limit number of instructions
    asDisassemblyBeforeAddress = asDisassemblyBeforeAddress[-dxConfig["uDisassemblyInstructionsBefore"]:];
    if asDisassemblyBeforeAddress:
      # Optionally highlight and describe instruction before the address:
      if sDescriptionOfInstructionBeforeAddress:
        sInstructionBeforeAddress = asDisassemblyBeforeAddress.pop(-1);
      asHTML += [fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, s) for s in asDisassemblyBeforeAddress];
      if sDescriptionOfInstructionBeforeAddress:
        asHTML.append(
          "%s <span class=\"Important\">// %s</span>" % \
              (fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sInstructionBeforeAddress, bImportant = True), \
              sDescriptionOfInstructionBeforeAddress)
        );
  if uDisassemblyBytesAfter > 0:
    while uDisassemblyBytesAfter > 0:
      # Get disassembly starting at address
      uStartAddress = uAddress;
      uEndAddress = uAddress + uDisassemblyBytesAfter;
      # Note: cannot use "u {start address} L{length}" as length is number of instructions, and we want number of bytes
      # so we use "u {start address} {end address}". Also, the start and end may not be in a valid memory region, so we
      # have to check before attempting to disassemble, or we may get an error. If either the start or end is in an
      # invalid region, no disassmbly is returned. In this case we move the END address closer to the end address, as
      # the former is more likely to be correct. We will try again and again, until we find that we cannot disassmble
      # anything.
      asDisassemblyAtAndAfterAddress = oProcess.fasExecuteCdbCommand(
        sCommand = ".if ($vvalid(0x%X, 1)) { .if ($vvalid(0x%X, 1)) { u 0x%X 0x%X; } };" % \
            (uStartAddress, uEndAddress, uStartAddress, uEndAddress),
        sComment = "Disassemble starting at address 0x%X" % uAddress, 
        bOutputIsInformative = True,
        bRetryOnTruncatedOutput = True,
      );
      if len(asDisassemblyAtAndAfterAddress) > 0:
        break;
      uDisassemblyBytesAfter -= 1;
    if asDisassemblyAtAndAfterAddress:
      assert len(asDisassemblyAtAndAfterAddress) >= 2, \
          "Unexpected short disassembly output:\r\n%s" % "\r\n".join(asDisassemblyAtAndAfterAddress);
      # The first line contains the address of the instruction
      if not asHTML:
        asHTML.append("(prior disassembly not possible)");
      # disassembly starts with a line containing the address/symbol:
      sAddressLine = asDisassemblyAtAndAfterAddress.pop(0);
      asHTML.append(fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sAddressLine));
      # First line of disassembly at address is important;
      sInstructionAtAddress = asDisassemblyAtAndAfterAddress.pop(0);
      sInstructionAtAddressHTML = fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, sInstructionAtAddress, bImportant = True);
      if sDescriptionOfInstructionAtAddress:
        sInstructionAtAddressHTML += " <span class=\"Important\">// %s</span>" % sDescriptionOfInstructionAtAddress;
      asHTML.append(sInstructionAtAddressHTML);
      # Limit the number of instructions, taking into account we already processed one:
      asDisassemblyAfterAddress = asDisassemblyAtAndAfterAddress[:dxConfig["uDisassemblyInstructionsAfter"] - 1];
      asHTML += [fsHTMLEncodeAndColorDisassemblyLine(oCdbWrapper, s) for s in asDisassemblyAfterAddress];
    elif asHTML:
      asHTML.append("(further disassembly not possible)");
  return "<br/>".join(asHTML);
