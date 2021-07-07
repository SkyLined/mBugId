import re;
from mWindowsSDK import *;

cCallRel32InstructionStructure = iStructureType8.fcCreateClass("CALL_rel32",
  (BYTE,        "u8Opcode"),
  (INT32,       "i32Displacement"),
);


grbNoSymbol = re.compile(
  rb"\A"                             # {
  rb"(?:"                            #   either {
    rb"[^!\+]+"                      #     sbModuleCdbId
    rb"\+0x" rb"[0-9`a-f]+"          #     "+0x" sOffset
    rb" \(" rb"[0-9`a-f]+" rb"\)"    #     " (" sAddress ")"
  rb"|"                              #   } or {
    rb"[0-9`a-f]+"                   #     sbAddress
  rb")" rb"\s*"                      #   } [whitespace]
  rb"\Z",                            # }
  re.I
);
grbSymbol = re.compile(
  rb"\A"                             # {
  rb"([^!]+)"                        #   (sbModuleCdbId)
  rb"!"                              #   "!"
  rb"(.+?)"                          #   (sFunctionSymbolName)
  rb"(?:"                            #   optional {
    rb"\+0x" rb"[0-9`a-f]+"          #     "+0x" sOffset
  rb")?"                             #   }
  rb" \(" rb"[0-9`a-f]+" rb"\)"      #   " (" sbAddress ")"
  rb"\s*"                            #   [whitespace]
  rb"\Z",                            # }
  re.I
);

def ft0oCallModuleAndFunctionFromCallInstructionForReturnAddress(oProcess, uReturnAddress):
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
  if oCallInstruction.u8Opcode != 0xE8:
    return None; # This opcode is not for the CALL instruction we can parse.
  # Find out the target of the call instruction (which is relative to the return address).
  uCallTargetAddress = uReturnAddress + oCallInstruction.i32Displacement;
  # Ask cdb for the symbol at the call target address. This is done twice: once to make sure symbols are loaded (which
  # may cause all kinds of random output that make the output unparsable) and once again to get parsable output.
  oProcess.fasbExecuteCdbCommand(
    sbCommand = b'.printf "%%y\\n", 0x%X;' % uCallTargetAddress, 
    sb0Comment = b"Get symbol for call target (warmup to make sure symbols are loaded)",
  );
  asbSymbolOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b'.printf "%%y\\n", 0x%X;' % uCallTargetAddress, 
    sb0Comment = b"Get symbol for call target",
  );
  # Output for an invalid (NULL) pointer:
  #   >00000000
  # Output for a module without symbol information (in x64 debugger):
  #   >nmozglue+0xf0c4 (73f1f0c4)
  # Output for a valid symbol (in x86 debugger, notice different header aligning):
  #   >ntdll!DbgBreakPoint (77ec1250)
  assert len(asbSymbolOutput) == 1, \
      "Unexpected get symbol output:\r\n%s" % "\r\n".join(asbSymbolOutput);
  if grbNoSymbol.match(asbSymbolOutput[0]):
    return None; # There is no symbol for the call target address.
  obSymbolOutput = grbSymbol.match(asbSymbolOutput[0]);
  assert obSymbolOutput, \
      "Unexpected symbol result:\r\n%s" % "\r\n".join(asbSymbolOutput);
  sbModuleCdbId, sbFunctionSymbol = obSymbolOutput.groups();
  oModule = oProcess.foGetOrCreateModuleForCdbId(sbModuleCdbId);
  oFunction = oModule.foGetOrCreateFunctionForSymbol(sbFunctionSymbol);
  return (oModule, oFunction);