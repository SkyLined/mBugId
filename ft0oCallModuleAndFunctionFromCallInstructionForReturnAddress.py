import re;
from mWindowsSDK import *;

cCallRel32InstructionStructure = iStructureType8.fcCreateClass("CALL_rel32",
  (BYTE,        "u8Opcode"),
  (INT32,       "i32Displacement"),
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
  sb0Symbol = oProcess.fsb0GetSymbolForAddress(uCallTargetAddress, b"CALL instruction at 0x%X target" % (uReturnAddress - 5));
  if sb0Symbol is None:
    return None;
  (
    u0Address,
    sb0UnloadedModuleFileName, o0Module, u0ModuleOffset,
    o0Function, i0OffsetFromStartOfFunction
  ) = oProcess.ftxSplitSymbolOrAddress(sb0Symbol);
  # We only accept "<module>!<function>" symbols:
  if (
    u0Address is not None
    or sb0UnloadedModuleFileName is not None
    or o0Module is None
    or u0ModuleOffset is not None
    or o0Function is None
    or i0OffsetFromStartOfFunction is not None
  ):
    return None;
  return (o0Module, o0Function);