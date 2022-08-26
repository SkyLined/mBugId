from mNotProvided import fAssertTypes;

from mWindowsAPI import fsHexNumber;

from .fo0GetDisassemblyForProcessAndCdbCommand import fo0GetDisassemblyForProcessAndCdbCommand;

def fo0GetInstructionForProcessAndAddress(
  oProcess,
  uAddress,
):
  fAssertTypes({
    "uAddress": (uAddress, int),
  });
  o0Disassembly = fo0GetDisassemblyForProcessAndCdbCommand(
    oProcess, 
    sbCommand = b"u 0x%X L%d" % (uAddress, 1), 
    sbComment = b"Disassemble instruction at %s" % (bytes(fsHexNumber(uAddress), "ascii", "strict"),),
  );
  return o0Disassembly.foGetInstruction(0) if o0Disassembly and len(o0Disassembly) == 1 else None;

