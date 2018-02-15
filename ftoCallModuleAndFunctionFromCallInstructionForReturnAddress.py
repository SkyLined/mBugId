import re;

from mWindowsAPI.mTypes import BYTE, fcStructure, INT32;

cCallRel32InstructionStructure = fcStructure("CALL_rel32",
  (BYTE,        "Opcode"),
  (INT32,       "Displacement"),
  uAlignmentBytes = 1, # The fields require no alignment.
);

def ftoCallModuleAndFunctionFromCallInstructionForReturnAddress(oProcess, uReturnAddress):
  # The symbol for a chunk of code may not be correct when using export symbols, or if we're in a small branch that is
  # not marked correctly in the pdb (cdb will report the closest symbol, which may be for another function!).
  #
  # We do have a return address for the function call and there should be a CALL instruction right before the
  # instruction that the return address points to. We may be able to determine the correct symbol for the function
  # from this CALL instruction. The only kind of CALL instruction handled by this code is the 0xE8 opcode with a DWORD
  # parameter (total: 5 bytes).
  # Find out if there is executable memory at the return address:
  oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uReturnAddress);
  if not oVirtualAllocation.bExecutable:
    return None; # This memory is not executable: this return address is invalid.
  # Find out if this executable memory can contain the CALL instruction we're expecting:
  uCallInstructionOffset = (uReturnAddress - 5) - oVirtualAllocation.uStartAddress;
  if uCallInstructionOffset < 0:
    return None; # The return addres points too close to the start of the memory to contain the call instruction.
  # Read the memory and find out if it does indeed contain a call instruction:
  oCallInstruction = oVirtualAllocation.foReadStructureForOffset(
    cStructure = cCallRel32InstructionStructure,
    uOffset = uCallInstructionOffset,
  );
  if oCallInstruction.Opcode != 0xE8:
    return None; # This opcode is not for the CALL instruction we can parse.
  # Find out the target of the call instruction (which is relative to the return address).
  uCallTargetAddress = uReturnAddress + oCallInstruction.Displacement;
  # Ask cdb for the symbol at the call target address. This is done twice: once to make sure symbols are loaded (which
  # may cause all kinds of random output that make the output unparsable) and once again to get parsable output.
  oProcess.fasExecuteCdbCommand(
    sCommand = '.printf "%%y\\n", 0x%X;' % uCallTargetAddress, 
    sComment = "Get symbol for call target (warmup to make sure symbols are loaded)",
  );
  asSymbolOutput = oProcess.fasExecuteCdbCommand(
    sCommand = '.printf "%%y\\n", 0x%X;' % uCallTargetAddress, 
    sComment = "Get symbol for call target (warmup to make sure symbols are loaded)",
  );
  # Output for an invalid (NULL) pointer:
  #   >00000000
  # Output for a module without symbol information (in x64 debugger):
  #   >nmozglue+0xf0c4 (73f1f0c4)
  # Output for a valid symbol (in x86 debugger, notice different header aligning):
  #   >ntdll!DbgBreakPoint (77ec1250)
  assert len(asSymbolOutput) == 1, \
      "Unexpected get symbol output:\r\n%s" % "\r\n".join(asSymbolOutput);
  if re.match(r"\A(?:%s)\s*\Z" % "|".join([
    "".join([
      r"[^!\+]+",                     #   sModuleCdbId
      r"\+0x" r"[0-9`a-f]+",          #   "+0x" sOffset
      r" \(" r"[0-9`a-f]+" r"\)",     #   " (" sAddress ")"
    ]),                               # - or -
    r"[0-9`a-f]+",                    #   sAddress
  ]),asSymbolOutput[0], re.I):
    return None; # There is no symbol for the call target address.
  oSymbolOutput = re.match(r"\A(?:%s\s*)\Z" % "".join([
    r"([^!]+)",                         # @sModuleCdbId
    r"!",                               # "!"
    r"(.+?)",                           # @sFunctionSymbolName
    r"(?:" r"\+0x" r"[0-9`a-f]+" r")?", # <optional> "+0x" sOffset </optional>
    r" \(" r"[0-9`a-f]+" r"\)",         # " (" sAddress ")"
  ]), asSymbolOutput[0], re.I);
  assert oSymbolOutput, \
      "Unexpected symbol result:\r\n%s" % "\r\n".join(asSymbolOutput);
  sModuleCdbId, sFunctionSymbolName = oSymbolOutput.groups();
  oModule = oProcess.foGetOrCreateModuleForCdbId(sModuleCdbId);
  oFunction = oModule.foGetOrCreateFunctionForName(sFunctionSymbolName);
  return (oModule, oFunction);