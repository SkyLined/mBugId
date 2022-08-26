from mNotProvided import fAssertTypes;

from mWindowsAPI import fsHexNumber;

from .fo0GetDisassemblyForProcessAndCdbCommand import fo0GetDisassemblyForProcessAndCdbCommand;

def fo0GetDisassemblyForProcessStartAddressAndNumberOfInstructions(
  oProcess,
  uStartAddress,
  uNumberOfInstructions,
):
  fAssertTypes({
    "uStartAddress": (uStartAddress, int),
    "uNumberOfInstructions": (uNumberOfInstructions, int),
  });
  assert 0 <= uNumberOfInstructions < 0x100, \
      "Request to disassemble %d instructions seems a little excessive!" % uNumberOfInstructions;
  return fo0GetDisassemblyForProcessAndCdbCommand(
    oProcess,
    sbCommand = b"u 0x%X L%d" % (uStartAddress, uNumberOfInstructions), 
    sbComment = b"Disassemble %d instructions at %s" % (uNumberOfInstructions, bytes(fsHexNumber(uStartAddress), "ascii", "strict")),
  );

