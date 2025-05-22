import re;

from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..mCP437 import fsCP437FromBytesString;

from .mAccessViolation import fUpdateReportForProcessThreadAccessViolationTypeIdAddressAndOptionalSize;

gbAssertOnUnhandledInstruction = True;
gbDebugOutput = False;

grbInstructionPointerDoesNotPointToAllocatedMemory = re.compile(
  rb"^"
  rb"([0-9`a-f]+)"            # (address)
  rb"\s+"                     # whitespace
  rb"\?\?"                    # "??"
  rb"\s+"                     # whitespace
  rb"\?\?\?"                  # "???"
);

grbInstruction = re.compile(
  rb"^"
  rb"[0-9`a-f]+"              # address
  rb"\s+"                     # whitespace
  rb"[0-9`a-f]+"              # opcode
  rb"\s+"                     # whitespace
  rb"(\w+)"                   # (instruction)
  rb"(?:"                     # optional{
    rb"\s+"                   #   whitespace
    rb"(.+?)?"                #   (operands)
    rb"(?:"                   #   optional either{
      rb"\ws:"                #     segment register ":"
      rb"(?:[0-9a-f`]{4}:)?"  #     optional { segment value ":" }
      rb"([0-9a-f`]+)"        #     (sAddress1)
      rb"="                   #     "="
      rb"(?:"                 #     either {
        rb"\?+"               #       "???????" <cannot be read>
      rb"|"                   #     } or {
        rb"([0-9`a-f]+)"      #       (sValue)  <memory at address can be read>
      rb"|"                   #     } or {
        rb"\{"                #       "{"
        rb".+"                #       symbol
        rb"\s+"               #       spaces
        rb"\(([0-9`a-f]+)\)"  #       "(" (sAddress2) ")"
        rb"\}"                #       "}"
      rb")"                   #     }
    rb"|"                     #   } or {
      rb"\{([0-9`a-f]+)\}"    #     "{" (sAddress3) "}"
    rb")?"                    #   }
  rb")?"                      # }
  rb"$"
);
def cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION(oBugReport, oProcess, oWindowsAPIThread, oException):
  oCdbWrapper = oProcess.oCdbWrapper;
  # Parameter[0] = access type (0 = read, 1 = write, 8 = execute)
  # Parameter[1] = address
  assert len(oException.auParameters) == 2, \
      "Unexpected number of access violation exception parameters (%d vs 2)" % len(oException.auParameters);
  # Access violation: add the type of operation and the location to the exception id.
  # EXCEPTION_RECORD structure documentation explains 0=R, 1=W, 8=E. I've found a few
  # more values that apply:
  sViolationTypeId = {
    0:"R", # reading from source operand failed
    1:"W", # writing to destination operand failed
    3:"?", # reading from or writing to the stack failed
    8:"E",
  }.get(oException.auParameters[0], "?");
  s0ViolationTypeNotes = None;
  uAccessViolationAddress = oException.auParameters[1];
  if sViolationTypeId == "E":
    # As far as I can tell, these reports are always accurate and need no
    pass;
  else:
    # Unfortunately, the exception record does not always represent reality.
    # * In x64 mode, some processors will throw an exception when you use an
    #   address larger than 0x7FFFFFFFFFFF and smaller than 0xFFFF800000000000,
    #   with address 0xFFFFFFFFFFFFFFFF and access type "read". This is not
    #   correct and needs to be handled correctly here.
    # * In x86 mode, some processors will throw an exception when you push/pop
    #   with an invalid stack pointer. The Parameter[0] will be 3 and the
    #   exception address may be wrong (e.g. 0 when it should be 0xFFFFFFFF)
    #
    # A partial work-around is to look at the disassembly of the last instruction
    # as output by cdb when you ask it to output disassembly and address after
    # each command. This output provides some hints as to the real details, which
    # we will use to correct the values obtained from the EXCEPTION_RECORD.
    oProcess.fasbExecuteCdbCommand(
      sbCommand = b".prompt_allow +dis +ea;",
      sb0Comment = b"Enable disassembly and address in cdb prompt",
    );
    # Do this twice in case the first time requires loading symbols, which can output junk that makes parsing output difficult.
    oProcess.fasbExecuteCdbCommand( \
      sbCommand = b"~s;",
      sb0Comment = b"Show disassembly and optional symbol loading stuff",
    );
    asbLastInstructionAndAddress = oProcess.fasbExecuteCdbCommand(
      sbCommand = b"~s;",
      sb0Comment = b"Show disassembly",
      bOutputIsInformative = True,
    );
    # Revert to not showing disassembly and address:
    oProcess.fasbExecuteCdbCommand( \
      sbCommand = b".prompt_allow -dis -ea;",
      sb0Comment = b"Revert to clean cdb prompt",
    );
    assert len(asbLastInstructionAndAddress) == 1, \
        "Unexpected last instruction output:\r\n%r" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbLastInstructionAndAddress);
    if gbDebugOutput: print("AV Instruction: %s" % str(asbLastInstructionAndAddress[0], "ascii", "replace"));
    # Example of output when Instruction Pointer does no point to allocated memory:
    # |00000000`7fffffff ??              ???
    obInstructionPointerDoesNotPointToAllocatedMemoryMatch = \
        grbInstructionPointerDoesNotPointToAllocatedMemory.match(asbLastInstructionAndAddress[0]);
    if obInstructionPointerDoesNotPointToAllocatedMemoryMatch:
      if gbDebugOutput: print("AV Instruction not in allocated memory => AVE");
      # "00000000`7fffffff ??              ???"
      #  ^^^^^^^^^^^^^^^^^-- address
      sbAddress = obInstructionPointerDoesNotPointToAllocatedMemoryMatch.group(1);
      uAccessViolationAddress = fu0ValueFromCdbHexOutput(sbAddress);
      assert uAccessViolationAddress, \
          "Cannot convert address %s to a value (taken from %s)" % (repr(sbAddress)[1:], repr(asbLastInstructionAndAddress[0])[1:]);
      sViolationTypeId = "E";
      s0ViolationTypeNotes = "the instruction pointer points to unallocated memory";
    else:
      # Examples of output for various other situations:
      #  Address           Opcode    sbInstruction asbOperands                       sb0AVAddress1     sb0Value         sb0AVAddress3 
      # |00007ffd`420b213e 488b14c2        mov     rdx,qword ptr [rdx+rax*8       ds:00007df5`ffb60000=????????????????
      # |60053594          ff7008          push    dword ptr [eax+8]         ds:002b:00000008=         ????????
      # |00007ff6`e7ab1204 ffe1            jmp     rcx                                                                  {c0c0c0c0`c0c0c0c0}
      # |00007ff9`b6f1a904 488b8d500d0000  mov     rcx,qword ptr [rbp+0D50h]      ss:00000244`4124f590=0000024441210240
      # |00007ffe`9f606c72 c3              ret
      # |00f986c8          5a              pop     edx
      # |00007ffc`f632ddcc c4a17e7f4c0980  vmovdqu ymmword ptr [rcx+r9-80h],ymm1  ds:0000015e`5e385ff2=61
      # TODO: Add example instruction with value for sb0AVAddress2
      obLastInstructionMatch = grbInstruction.match(asbLastInstructionAndAddress[0]);
      # I'm tempted to assert here but I that may prevent analysis of issues and
      # getting some analysis, even if incorrect is better than getting none.
      if obLastInstructionMatch:
        (sbInstruction, sb0Operands, sb0AVAddress1, sb0Value, sb0AVAddress2, sb0AVAddress3) = \
            obLastInstructionMatch.groups();
        asbOperands = sb0Operands.split(b",") if sb0Operands else [];
        sb0AVAddress = sb0AVAddress1 or sb0AVAddress2 or sb0AVAddress3;
        if sb0AVAddress:
          uAccessViolationAddress = fu0ValueFromCdbHexOutput(sb0AVAddress);
          assert uAccessViolationAddress, \
              "Cannot convert address %s to a value (taken from %s)" % (repr(sb0AVAddress)[1:], repr(asbLastInstructionAndAddress[0])[1:]);
        if sb0AVAddress3 is not None: 
          # This is only expected to happens when an instruction changes *IP to
          # point to an address that can not be executed. There's only two known
          # instructions that do this: call and jmp.
          assert sbInstruction in [b"call", b"jmp"], \
              "Unexpected instruction %s that resulted in executing at address %s" % (repr(sbInstruction)[1:], repr(sb0AVAddress3)[1:]);
          sViolationTypeId = "E";
          s0ViolationTypeNotes = "the %s instruction's destination points to unallocated memory" % str(sbInstruction, "ascii", "strict");
          if gbDebugOutput: print("AV %s Instruction destination does not point to executable memory => AV%s @ %s" % (
            str(sbInstruction, "ascii", "strict"),
            sViolationTypeId,
            str(sbAddress, "ascii", "strict"),
          ));
        elif sbInstruction in [b"dec", b"inc", b"neg", b"not", b"shl", b"shr"]:
          # These instructions always read and then write to memory. We classify
          # this as a write AV even if the address does not reference readable
          # memory, in which case the AV was actually caused by the read.
          sViolationTypeId = "W";
          s0ViolationTypeNotes = "the %s instruction reads and writes to the same memory" % str(sbInstruction, "ascii", "strict");
          if gbDebugOutput: print("AV %s Instruction always writes to memory => AV%s at" % (
            str(sbInstruction, "ascii", "strict"),
            sViolationTypeId,
            uAccessViolationAddress,
          ));
        elif sbInstruction in [b"call", b"push"]:
          # The first operand is the source, the stack is the destination.
          # If the first argument does not reference memory it must
          # be a write AV on the stack, otherwise we do not know.
          # We could find out by seeing what Virtual Allocation exists at *SP
          # but that is complex and doesn't seem worth implementing at this time.
          if b"[" in asbOperands[0]:
            sViolationTypeId = "?";
            s0ViolationTypeNotes = "the %s instruction reads from memory and it writes to the stack" % str(sbInstruction, "ascii", "strict");
            if gbDebugOutput: print("AV %s Instruction destination operand %s references memory => AV%s at 0x%X" % (
              str(sbInstruction, "ascii", "replace"),
              str(asbOperands[0], "ascii", "replace"),
              sViolationTypeId,
              uAccessViolationAddress,
            ));
          else:
            sViolationTypeId = "W";
            s0ViolationTypeNotes = "the %s instruction writes to the stack" % str(sbInstruction, "ascii", "strict");
            # A call or push instruction would decrease the stack pointer by the
            # size of a pointer for the ISA and store a value at the new
            # address. The exception must therefore have happened at the current
            # stack pointer address minus the size of a pointer.
            iAccessViolationAddress = oProcess.fuGetValueForStackPointer() - oProcess.uPointerSizeInBytes;
            # This might be negative, so we need to wrap it around the address
            # space:
            uAccessViolationAddress = iAccessViolationAddress + (0 if iAccessViolationAddress >= 0 else (1 << oProcess.uPointerSizeInBits));
            if gbDebugOutput: print("AV %s Instruction destination operand %s does not reference memory => AV%s @ stack pointer 0x%X" % (
              str(sbInstruction, "ascii", "replace"),
              str(asbOperands[0], "ascii", "replace"),
              sViolationTypeId,
              uAccessViolationAddress,
            ));
        elif sbInstruction in [b"cmp", b"idiv", b"imul", b"jmp", b"test"]:
          # These instructions' destination register must be a register, so they
          # can only have read from memory and this must be a read AV.
          sViolationTypeId = "R";
          s0ViolationTypeNotes = "the %s instruction only reads from memory" % str(sbInstruction, "ascii", "strict");
          if gbDebugOutput: print("AV %s Instruction only reads from memory => AV%s at 0x%X" % (
            str(sbInstruction, "ascii", "strict"),
            sViolationTypeId,
            uAccessViolationAddress,
          ));
        elif sbInstruction in [
          b"add", b"sub",
          b"and", b"or",
          b"mov", b"movsx", b"movzx", 
          b"movdqa", b"movdqu",
          b"vmovdqa", b"vmovdqu", b"vmovsh", b"vmovw",
          b"xor",
        ]:
          # The first operand is the destination, if it references memory it must
          # be a write AV, otherwise it must be a read AV.
          if b"[" in asbOperands[0]:
            sViolationTypeId = "W";
            s0ViolationTypeNotes = "the %s instruction's destination writes to memory" % str(sbInstruction, "ascii", "strict");
          else:
            sViolationTypeId = "R";
            s0ViolationTypeNotes = "the %s instruction's source reads from memory" % str(sbInstruction, "ascii", "strict");
          if gbDebugOutput: print("AV %s Instruction destination operand %s %s memory => AV%s at 0x%X" % (
            str(sbInstruction, "ascii", "strict"),
            str(asbOperands[0], "ascii", "replace"),
            "references" if b"[" in asbOperands[0] else "does not reference",
            sViolationTypeId,
            uAccessViolationAddress,
          ));
        elif sbInstruction in [b"pop"]:
          # The first operand is the destination, the stack is the source.
          # If the first argument does not reference memory it must
          # be a read AV on the stack, otherwise we do not know.
          # We could find out but that is complex and doesn't seem worth
          # implementing at this time.
          if b"[" in asbOperands[0]:
            sViolationTypeId = "?";
            s0ViolationTypeNotes = "the %s instruction writes to memory and it read from the stack" % str(sbInstruction, "ascii", "strict");
            if gbDebugOutput: print("AV %s Instruction destination operand %s references memory => AV%s @ 0x%X" % (
              str(sbInstruction, "ascii", "replace"),
              str(asbOperands[0], "ascii", "replace"),
              sViolationTypeId,
              uAccessViolationAddress,
            ));
          else:
            sViolationTypeId = "R";
            uAccessViolationAddress = oProcess.fuGetValueForStackPointer();
            s0ViolationTypeNotes = "the %s instruction reads from the stack" % str(sbInstruction, "ascii", "strict");
            if gbDebugOutput: print("AV %s Instruction destination operand %s does not reference memory => AV%s @ stack pointer 0x%X" % (
              str(sbInstruction, "ascii", "replace"),
              str(asbOperands[0], "ascii", "replace"),
              sViolationTypeId,
              uAccessViolationAddress,
            ));
        elif sbInstruction in [b"ret"]:
          sViolationTypeId = "R";
          uAccessViolationAddress = oProcess.fuGetValueForStackPointer();
          s0ViolationTypeNotes = "the %s instruction reads from the stack" % str(sbInstruction, "ascii", "strict");
          if gbDebugOutput: print("AV %s Instruction does not reference memory => AV%s @ stack pointer 0x%X" % (
            str(sbInstruction, "ascii", "replace"),
            sViolationTypeId,
            uAccessViolationAddress,
          ));
        elif gbAssertOnUnhandledInstruction:
          raise AssertionError("Unhandled instruction: %s" % repr(asbLastInstructionAndAddress[0])[1:]);
        else:
          if gbDebugOutput: print("AV %s Instruction not handled => AV?" % repr(sbInstruction));
          # TODO: parse more instructions.
          # In the mean time, if we encounter the below, it means there is some confusion about
          # an invalid address on an x64 processor:
          if oException.auParameters[1] == 0xFFFFFFFFFFFFFFFF and sViolationTypeId == "R":
            sViolationTypeId = "?";
            s0ViolationTypeNotes = "the type of access must be read or write, but cannot be determined";
  oBugReport.fAddMemoryRemark("Access violation", uAccessViolationAddress, None); # TODO Find out size of access
  
  if sViolationTypeId == "E":
    # Hide the top stack frame if it is for the address at which the execute access violation happened:
    if oBugReport and oBugReport.o0Stack and oBugReport.o0Stack.aoFrames \
        and oBugReport.o0Stack.aoFrames[0].u0InstructionPointer is uAccessViolationAddress:
      oBugReport.o0Stack.aoFrames[0].s0IsHiddenBecause = "called address";
  
  fUpdateReportForProcessThreadAccessViolationTypeIdAddressAndOptionalSize(
    oCdbWrapper,
    oBugReport,
    oProcess,
    oWindowsAPIThread,
    sViolationTypeId,
    uAccessViolationAddress,
    u0AccessViolationSize = None, # NOT AVAILABLE (YET).
  );

  if s0ViolationTypeNotes:
    oBugReport.s0BugDescription += " (%s)" % s0ViolationTypeNotes; # Shouldn't be None
  return oBugReport;

