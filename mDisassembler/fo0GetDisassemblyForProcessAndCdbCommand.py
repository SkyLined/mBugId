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
  rb"("
    rb"\[inlined in "         # "[inlined in "
    rb"(\w+!.*)"              # <<<symbol [source]>>> 
    rb"\]?"                   # "]"
  rb"|"
    rb"(\w+!.*)"              # <<<symbol [source]>>> 
  rb")"
  rb":"
  rb"\Z"
);

grbMemoryAccessErrorDisassemblyLine = re.compile(
  rb"\A"
  rb"([0-9`a-f]+)"            # <<<address>>>
  rb"\s+"                     # whitespace
  rb"\?\?"                    # "??"
  rb"\s+"                     # whitespace
  rb"\?\?\?"                  # "???"
);
grbInvalidInstructionDisassemblyLine = re.compile(
  rb"\A"
  rb"([0-9`a-f]+)"            # <<<address>>>
  rb"\s+"                     # whitespace
  rb"([0-9a-f]+)"             # <<<instruction bytes>>>
  rb"\s+"                     # whitespace
  rb"\?\?\?"                  # "???"
);
grbInstructionDisassemblyLine = re.compile(
  rb"\A"
  rb"([0-9`a-f]+)"            # <<<address>>>
  rb"\s+"                     # whitespace
  rb"([0-9a-f]+)"             # <<<instruction bytes>>>
  rb"\s+"                     # whitespace
  rb"(\w+)"                   # <<<instruction name>>>
  rb"(?:"                     # optional {
    rb"\s+"                   #   whitespace
    rb"(.*)"                  #   <<<instruction arguments>>>
  rb")?"                      # }
  rb"\Z"
);

def fo0GetDisassemblyForProcessAndCdbCommand(
  oProcess,
  sbCommand,
  sbComment,
):
  try:
    asbDisassemblyOutput = oProcess.fasbExecuteCdbCommand(
      sbCommand = sbCommand, 
      sb0Comment = sbComment,
    );
  except oProcess.oCdbWrapper.cEndOfCommandOutputMarkerMissingException as oException:
    # Memory access errors will stop cdb from executing more commands,
    # so the end-of-command-output marker will be missing.
    asbDisassemblyOutput = oException.asbCommandOutput;
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
      or grbMemoryAccessErrorDisassemblyLine.match(sbDisassemblyOutputLine)
    ):
      ob0InvalidInstructionMatch = grbInvalidInstructionDisassemblyLine.match(sbDisassemblyOutputLine);
      if ob0InvalidInstructionMatch:
        (sbAddress, sbHexBytes) = ob0InvalidInstructionMatch.groups();
        uAddress = fu0ValueFromCdbHexOutput(sbAddress);
        sbBytes = bytes.fromhex(str(sbHexBytes, "ascii", "strict")); # fromhex should just support bytes as input already.
        aoInstructions.append(cInstruction(uAddress, sbBytes, b"???", tuple()));
      else:
        ob0InstructionMatch = grbInstructionDisassemblyLine.match(sbDisassemblyOutputLine);
        assert ob0InstructionMatch, \
            "Unrecognised instruction disassembly line:\r\n%s" % sbDisassemblyOutputLine;
        # Grab info from current instruction (name and arguments):
        (sbAddress, sbHexBytes, sbName, sb0Arguments) = ob0InstructionMatch.groups();
        uAddress = fu0ValueFromCdbHexOutput(sbAddress);
        sbBytes = bytes.fromhex(str(sbHexBytes, "ascii", "strict")); # fromhex should just support bytes as input already.
        if sb0Arguments:
          # Arguments are separated by commas. Symbols in the arguments can
          # also contain commas. AFAICT symbols only contain commas inside
          # brackets. So, we need to determine if we are inside a bracket in
          # order to determine in a comma marks the end of an argument or not.
          asbArguments = [b""];
          uNestedBrackets = 0;
          for uChar in sb0Arguments:
            sChar = chr(uChar);
            if sChar in "<[{":
              uNestedBrackets += 1;
            elif sChar in "}]>":
              uNestedBrackets -= 1;
            if uNestedBrackets == 0 and sChar == ",":
              asbArguments.append(b"");
            elif uNestedBrackets == 0 and sChar == " " and asbArguments[-1] == b"":
              pass; # space following a comma is ignored.
            else:
              asbArguments[-1] += bytes((uChar,));
          tsbArguments = tuple(asbArguments);
        else:
          tsbArguments = tuple();
        aoInstructions.append(cInstruction(uAddress, sbBytes, sbName, tsbArguments));
  return cDisassembly(aoInstructions);

