import re;

from mNotProvided import fAssertTypes;

from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;

from .cDisassembly import cDisassembly;
from .cInstruction import cInstruction;

grbMemoryAccessErrorLine = re.compile(
  rb"\A"
  rb"\s*\^ Memory access error in '.+'"
  rb"\Z"
);

grbSymbolLine = re.compile(
  rb"\A"
  rb"\w+!.*"
  rb"\Z"
);

grbInvalidInstructionDisassemblyLine = re.compile(
  rb"\A"
  rb"([0-9`a-f]+)"            # <<<address>>>
  rb"\s+"                     # whitespace
  rb"([0-9a-f]+)"             # instruction bytes
  rb"\s+"                     # whitespace
  rb"\?\?\?"
);
grbInstructionDisassemblyLine = re.compile(
  rb"\A"
  rb"([0-9`a-f]+)"            # <<<address>>>
  rb"\s+"                     # whitespace
  rb"([0-9a-f]+)"             # instruction bytes
  rb"\s+"                     # whitespace
  rb"(\w+)"                   # <<<opcode name>>>
  rb"(?:"                     # optional {
    rb"\s+"                   #   whitespace
    rb"(.*)"                  #   <<<arguments>>>
  rb")?"                      # }
  rb"\Z"
);

def fo0GetDisassemblyFromCdbOutput(asbDisassemblyOutput):
  fAssertTypes({
    "asbDisassemblyOutput": (asbDisassemblyOutput, [bytes]),
  });
  if len(asbDisassemblyOutput) == 0:
    return None;
  aoInstructions = [];
  for sbDisassemblyOutputLine in asbDisassemblyOutput:
    if not (
      grbMemoryAccessErrorLine.match(sbDisassemblyOutputLine)
      or grbSymbolLine.match(sbDisassemblyOutputLine)
      or grbInvalidInstructionDisassemblyLine.match(sbDisassemblyOutputLine)
    ):
      ob0InstructionMatch = grbInstructionDisassemblyLine.match(sbDisassemblyOutputLine);
      assert ob0InstructionMatch, \
          "Unrecognised instruction disassembly line:\r\n%s" % sbDisassemblyOutputLine;
      # Grab info from current instruction (name and arguments):
      (sbAddress, sbHexBytes, sbName, sb0Arguments) = ob0InstructionMatch.groups();
      uAddress = fu0ValueFromCdbHexOutput(sbAddress);
      sbBytes = bytes.fromhex(str(sbHexBytes, "ascii", "strict")); # fromhex should just support bytes as input already.
      tsbArguments = tuple(s.strip() for s in sb0Arguments.split(b",")) if sb0Arguments else tuple();
      aoInstructions.append(cInstruction(uAddress, sbBytes, sbName, tsbArguments));
  return cDisassembly(aoInstructions);

