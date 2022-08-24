from mNotProvided import fAssertTypes;

from .fo0GetDisassemblyFromCdbOutput import fo0GetDisassemblyFromCdbOutput;

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
  asbDisassemblyOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b"u 0x%X L%d" % (uStartAddress, uNumberOfInstructions), 
    sb0Comment = b"Disassemble %d instructions at %d" % (uNumberOfInstructions, uStartAddress),
  );
  return fo0GetDisassemblyFromCdbOutput(asbDisassemblyOutput);

