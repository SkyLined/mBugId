import re;
from mWindowsSDK import *;

gbDebugOutput = False;

cCall_Near_rel32off_InstructionStructure = iStructureType8.fcCreateClass("Call_Near_rel32off",
  (BYTE,        "u8Opcode"),
  (INT32,       "i32Offset"),
);
cCall_Near_regmem32_InstructionStructure = iStructureType8.fcCreateClass("CALL_Near_regmem32",
  (BYTE,        "u8Opcode"),
  (BYTE,        "u8ModRM"),
  (INT32,       "i32Offset"),
);

def cProcess_fu0GetTargetAddressForCallInstructionReturnAddress(oProcess, uReturnAddress):
  # Find out if there is executable memory at the return address:
  o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uReturnAddress);
  if not o0VirtualAllocation:
    if gbDebugOutput: print ("No CALL instruction found for return address 0x%X: no virtual allocation at return address." % (uReturnAddress,));
    return None;
  if not o0VirtualAllocation.bExecutable:
    if gbDebugOutput: print ("No CALL instruction found for return address 0x%X: non-executable virtual allocation %s" % (uReturnAddress, o0VirtualAllocation));
    return None;
  ##################################################################
  # We can guess at the CALL instruction used to make this call and see if we can find it right before the return
  # address. This means we need to make sure the call instruction is entirely within the virtual allocation first,
  # and then read it to check the opcode.
  def fo0ReadCallInstruction(cCallInstructionStructure, uOpcode):
    uInstructionAddress = uReturnAddress - cCallInstructionStructure.fuGetSize();
    uCallInstructionOffset = uInstructionAddress - o0VirtualAllocation.uStartAddress;
    if uCallInstructionOffset < 0:
      if gbDebugOutput: print ("No %s instruction found for return address 0x%X: instruction would start before virtual allocation %s" % \
            (cCallInstructionStructure.__name__, uInstructionAddress, o0VirtualAllocation));
      return None;
    # Read the memory and find out if it does indeed contain a call instruction:
    oCallInstruction = o0VirtualAllocation.foReadStructureForOffset(
      cStructure = cCallInstructionStructure,
      uOffset = uCallInstructionOffset,
    );
    if oCallInstruction.u8Opcode != uOpcode:
      if gbDebugOutput: print ("No %s instruction found at 0x%X: opcode 0x%02X != 0x%02X" % \
          (cCallInstructionStructure.__name__, uInstructionAddress, oCallInstruction.u8Opcode.fuGetValue(), uOpcode));
      return None;
    return oCallInstruction;
  #####################
  # Some CALL instructions reference an address in memory; we need to read that address to see what is ebing called.
  def fu0ReadAddressFromMemory(cAddressType, uMemoryAddress):
    o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uMemoryAddress);
    if not o0VirtualAllocation.bAllocated:
      if gbDebugOutput: print ("No %s address found for memory address 0x%X: no memory allocated" % \
            (cAddressType.__name__, uMemoryAddress, o0VirtualAllocation));
      return None;
    if not o0VirtualAllocation.bReadable:
      if gbDebugOutput: print ("No %s address found for memory address 0x%X: non-readable virtual allocation %s" % \
            (cAddressType.__name__, uMemoryAddress, o0VirtualAllocation));
      return None;
    if uMemoryAddress >= o0VirtualAllocation.uEndAddress:
      if gbDebugOutput: print ("No %s address found for memory address 0x%X: address ends outside virtual allocation %s" % \
            (cAddressType.__name__, uMemoryAddress, o0VirtualAllocation));
      return None;
    # Read the memory and find out if it does indeed contain a call instruction:
    oAddress = o0VirtualAllocation.foReadStructureForOffset(
      cStructure = cAddressType,
      uOffset = uMemoryAddress - o0VirtualAllocation.uStartAddress,
    );
    return oAddress.fuGetValue();
  ##### See if this is "E8 XXXXXXXX": CALL RIP+OFFSET32
  o0CallInstructionStructure = fo0ReadCallInstruction(cCall_Near_rel32off_InstructionStructure, 0xE8);
  if o0CallInstructionStructure:
    # Find out the target of the call instruction; it is encoded as the offset from the address of the end of the CALL instruction).
    uCallTargetAddress = uReturnAddress + o0CallInstructionStructure.i32Offset;
    if gbDebugOutput: print ("CALL NEAR %02X IP+%04X found for return address 0x%X: address = 0x%08X." % (
      o0CallInstructionStructure.u8Opcode.fuGetValue(),
      o0CallInstructionStructure.i32Offset.fuGetValue(),
      uReturnAddress,
      uCallTargetAddress,
    ));
    return uCallTargetAddress;
  ##### See if this is "FF YY XXXXXXXX": CALL [EIP+OFFSET32]
  o0CallInstructionStructure = fo0ReadCallInstruction(cCall_Near_regmem32_InstructionStructure, 0xFF);
  if o0CallInstructionStructure:
    if o0CallInstructionStructure.u8ModRM == 0x15:
      # Find out the target of the call instruction; it is encoded as the offset from the address of the end of the CALL instruction).
      uCallMemoryAddress = uReturnAddress + o0CallInstructionStructure.i32Offset;
      u0CallTargetAddress = fu0ReadAddressFromMemory(UINT64, uCallMemoryAddress);
    else:
      if gbDebugOutput: print ("No %s address found for return address 0x%X: ModRM byte 0x%02 not handled." % \
            (cCall_Near_regmem32_InstructionStructure.__name__, uReturnAddress, o0CallInstructionStructure.u8ModRM));
      return None;
    if gbDebugOutput: print ("CALL NEAR %02X %02X [IP+%04X] found for return address 0x%X: address [%08X] = 0x%08X." % (
      o0CallInstructionStructure.u8Opcode.fuGetValue(),
      o0CallInstructionStructure.u8ModRM.fuGetValue(),
      o0CallInstructionStructure.i32Offset.fuGetValue(),
      uReturnAddress,
      uCallMemoryAddress,
      u0CallTargetAddress,
    ));
    return u0CallTargetAddress;
  
  if gbDebugOutput:
    rbIgnoredMemoryAccessError = re.compile(
      rb"\A"
      rb"\s*\^ Memory access error in '.+'"
      rb"\Z"
    );
    asbDisassemblyBeforeAddress = oProcess.fasbExecuteCdbCommand(
      sbCommand = b"u 0x%X 0x%X;" % (uReturnAddress - 32, uReturnAddress),
      sb0Comment = b"Disassemble up to address 0x%X" % uReturnAddress,
      bOutputIsInformative = False,
      bRetryOnTruncatedOutput = True,
      rb0IgnoredErrors = rbIgnoredMemoryAccessError,
    );
    for sbLine in asbDisassemblyBeforeAddress[-8:]:
      print ("  %s" % str(sbLine, "ascii", "strict"));
  return None; # This opcode is not for the CALL instruction we can parse.
