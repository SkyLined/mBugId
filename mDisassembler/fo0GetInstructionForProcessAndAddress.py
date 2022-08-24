from mNotProvided import fAssertTypes;

from .fo0GetDisassemblyFromCdbOutput import fo0GetDisassemblyFromCdbOutput;

def fo0GetInstructionForProcessAndAddress(
  oProcess,
  uAddress,
):
  fAssertTypes({
    "uAddress": (uAddress, int),
  });
  asbDisassemblyOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b"u 0x%X L%d" % (uAddress, 1), 
    sb0Comment = b"Disassemble instruction at %d" % (uAddress,),
  );
  o0Disassembly = fo0GetDisassemblyFromCdbOutput(asbDisassemblyOutput);
  return o0Disassembly.foGetInstruction(0) if o0Disassembly and len(o0Disassembly) == 1 else None;

