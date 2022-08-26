from mNotProvided import fAssertTypes;

from mWindowsAPI import fsHexNumber;

from .fo0GetDisassemblyForProcessAndCdbCommand import fo0GetDisassemblyForProcessAndCdbCommand;

def fo0GetInstructionForProcessAndBeforeAddress(
  oProcess,
  uAddress,
):
  fAssertTypes({
    "uAddress": (uAddress, int),
  });
  # Disassemble the 32 bytes before the address; we're hoping that is enough to
  # "align" the disasssembly by the time it gets to the instruction we want
  # but this is not guaranteed.
  o0Disassembly = fo0GetDisassemblyForProcessAndCdbCommand(
    oProcess, 
    sbCommand = b"u 0x%X 0x%X" % (uAddress - 32, uAddress), 
    sbComment = b"Disassemble instructions before %s" % (bytes(fsHexNumber(uAddress), "ascii", "strict"),),
  );
  if o0Disassembly is None or o0Disassembly.uLength == 0:
    return None;
  # Check if one of the instructions in the disassembly ends at the address.
  # It is not guaranteed that that was indeed the last executed instruction
  # but it is likely (sorry, no idea how likely).
  for uIndex in range(len(o0Disassembly)):
    oInstruction = o0Disassembly.foGetInstruction(uIndex);
    if oInstruction.uAddress + oInstruction.uSize == uAddress:
      return oInstruction;
  return None;

