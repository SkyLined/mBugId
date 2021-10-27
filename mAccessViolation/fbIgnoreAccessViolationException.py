import re;

from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;

gduSizeInBits_by_sbRegisterName = {
  b"rax":    64, b"eax":    32, b"ax":     16, b"al":      8, b"ah": 8,
  b"rbx":    64, b"ebx":    32, b"bx":     16, b"bl":      8, b"bh": 8,
  b"rcx":    64, b"ecx":    32, b"cx":     16, b"cl":      8, b"ch": 8,
  b"rdx":    64, b"edx":    32, b"dx":     16, b"dl":      8, b"dh": 8,
  b"rsi":    64, b"esi":    32, b"si":     16, b"sil":     8,
  b"rdi":    64, b"edi":    32, b"di":     16, b"dil":     8,
  b"rbp":    64, b"ebp":    32, b"bp":     16, b"bpl":     8,
  b"rsp":    64, b"esp":    32, b"sp":     16, b"spl":     8,
  b"rip":    64, b"eip":    32, b"ip":     16,
  b"r8":     64, b"r8d":    32, b"r8w":    16, b"r8b":     8,
  b"r9":     64, b"r9d":    32, b"r9w":    16, b"r9b":     8,
  b"r10":    64, b"r10d":   32, b"r10w":   16, b"r10b":    8,
  b"r11":    64, b"r11d":   32, b"r11w":   16, b"r11b":    8,
  b"r12":    64, b"r12d":   32, b"r12w":   16, b"r12b":    8,
  b"r13":    64, b"r13d":   32, b"r13w":   16, b"r13b":    8,
  b"r14":    64, b"r14d":   32, b"r14w":   16, b"r14b":    8,
  b"r15":    64, b"r15d":   32, b"r15w":   16, b"r15b":    8,
  b"mm0":    64, b"mm1":    64, b"mm2":    64, b"mm3":    64,
  b"mm4":    64, b"mm5":    64, b"mm6":    64, b"mm7":    64,
  b"xmm0":  128, b"xmm1":  128, b"xmm2":  128, b"xmm3":  128,
  b"xmm4":  128, b"xmm5":  128, b"xmm6":  128, b"xmm7":  128,
  b"xmm8":  128, b"xmm9":  128, b"xmm10": 128, b"xmm11": 128,
  b"xmm12": 128, b"xmm13": 128, b"xmm14": 128, b"xmm15": 128,
# No support for xmm16-31 or ymm in mWindowsAPI yet, as there is no documentation on where these are stored in the
# CONTEXT struct used by Get-/SetThreadContext.
  b"xmm16": 128, b"xmm17": 128, b"xmm18": 128, b"xmm19": 128,
  b"xmm20": 128, b"xmm21": 128, b"xmm22": 128, b"xmm23": 128,
  b"xmm24": 128, b"xmm25": 128, b"xmm26": 128, b"xmm27": 128,
  b"xmm28": 128, b"xmm29": 128, b"xmm30": 128, b"xmm31": 128, 
  b"ymm0":  256, b"ymm1":  256, b"ymm2":  256,  b"ymm3": 256,
  b"ymm4":  256, b"ymm5":  256, b"ymm6":  256,  b"ymm7": 256,
  b"ymm8":  256, b"ymm9":  256, b"ymm10": 256, b"ymm11": 256,
  b"ymm12": 256, b"ymm13": 256, b"ymm14": 256, b"ymm15": 256,
  b"ymm16": 256, b"ymm17": 256, b"ymm18": 256, b"ymm19": 256,
  b"ymm20": 256, b"ymm21": 256, b"ymm22": 256, b"ymm23": 256,
  b"ymm24": 256, b"ymm25": 256, b"ymm26": 256, b"ymm27": 256,
  b"ymm28": 256, b"ymm29": 256, b"ymm30": 256, b"ymm31": 256, 
};
gduSizeInBits_by_sbPointerTargetSize = {
  # No support for ymm yet.
  b"byte": 8, b"word": 16, b"dword": 32, b"qword": 64, b"mmword": 64, b"xmmword": 128, b"ymmword": 256,
};

grbInstruction = re.compile(
  rb"^"
  rb"([0-9`a-f]+)"            # <<<address>>>
  rb"\s+"                     # whitespace
  rb"[0-9`a-f]+"              # instruction bytes
  rb"\s+"                     # whitespace
  rb"(\w+)"                   # <<<opcode name>>>
  rb"(?:"                     # optional {
    rb"\s+"                   #   whitespace
    rb"(.*)"                  #   <<<arguments>>>
  rb")?"                      # }
  rb"$"
);

grbInstructionPointerArgumentTargetSize = re.compile(
  rb"^"               #
  rb"("               # <<< either {
    rb"byte"          #  "byte"
  rb"|"               # } or {
    rb"(?:"           #   optional either {
      rb"d"           #     "d"
    rb"|"             #   } or {
      rb"q"           #     "q"
    rb"|"             #   } or {
      rb"[xy]?mm"     #     "xmm"/"ymm"
    rb")?"            #   }
    rb"word"          #   "word"
  rb")"               # } >>>
  rb" ptr \["         # " ptr ["
  rb".*"              #   anything
  rb"\]"              # "]"
  rb"$"               #
);

def fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess, oThread, sViolationTypeId, uPointerSizedValue = None):
  if sViolationTypeId == "E":
    # The application is attempting to execute code at an address that does not point to executable memory; this cannot
    # be ignored.
#    print "@@@ sViolationTypeId == \"E\"";
    return False;
  # See if we can fake execution of the current instruction, so we can continue the application as if it had been
  # executed without actually executing it.
  sInstructionPointerRegister = {"x86": "eip", "x64": "rip"}[oProcess.sISA];
  u0InstructionPointer = oThread.fu0GetRegister(b"*ip");
  if u0InstructionPointer is None:
    # We cannot get the instruction pointer for this thread; it must be terminated and cannot be continued.
#    print "@@@ u0InstructionPointer == None";
    return False;
  uInstructionPointer = u0InstructionPointer;
  o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uInstructionPointer);
  if not o0VirtualAllocation or not o0VirtualAllocation.bExecutable:
    # This can happen if a call/return sets the instruction pointer to a corrupted value; it may point to a region that
    # is not allocated, or contains non-executable data. (e.g. a poisoned value)
#    print "@@@ o0VirtualAllocation.bExecutable == False";
    return False; # This memory is not executable: we cannot continue execution.
  asbDiassemblyOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b"u 0x%X L2" % uInstructionPointer, 
    sb0Comment = b"Get information about the instruction that caused the AV",
  );
  if len(asbDiassemblyOutput) == 0:
    # The instruction pointer does not point to valid memory.
#    print "@@@ asbDiassemblyOutput == []";
    return False;
  assert len(asbDiassemblyOutput) == 3, \
      "Expected 3 lines of disassembly, got %d:\r\n%s" % (len(asbDiassemblyOutput), b"\r\n".join(asbDiassemblyOutput));
  (sbSymbol_unused, sbCurrentInstruction, sbNextInstruction) = asbDiassemblyOutput;
  # Grab info from current instruction (name and arguments):
  obCurrentInstructionMatch = grbInstruction.match(sbCurrentInstruction);
  assert obCurrentInstructionMatch, \
      "Unrecognised diassembly output second line:\r\n%s" % b"\r\n".join(asbDiassemblyOutput);
  (sbCurrentInstructionAddress_unused, sbCurrentInstructionName, sbCurrentInstructionArguments) = \
      obCurrentInstructionMatch.groups();
  if sbCurrentInstructionName not in [b"add", b"addsd", b"call", b"cmp", b"jmp", b"mov", b"movzx", b"movsd", b"mulsd", b"sub", b"subsd"]:
#    print "Cannot handle instruction %s:\r\n%s" % (repr(sbCurrentInstructionName), b"\r\n".join(asbDiassemblyOutput));
#    print "@@@ sbCurrentInstructionName == %s" % repr(sbCurrentInstructionName);
    return False;
  # Grab info from next instruction (it's starting address):
  obNextInstructionMatch = grbInstruction.match(sbNextInstruction);
  assert obNextInstructionMatch, \
      "Unrecognised diassembly output third line:\r\n%s" % b"\r\n".join(asbDiassemblyOutput);
  (sbNextInstructionAddress, sbNextInstructionName_unused, sbNextInstructionArguments_unused) = obNextInstructionMatch.groups();
  uNextInstructionAddress = fu0ValueFromCdbHexOutput(sbNextInstructionAddress); # Never returns None
  # We do not care about the difference between these operations; for writes, we simply discard the value. For reads
  # we assume that we have full control over the memory at the specified address, and thus full control over the
  # result stored in the register, so we just fake reading a poisoned value.
  asbCurrentInstructionArguments = sbCurrentInstructionArguments.split(b",");
  if sbCurrentInstructionName in [b"call", b"jmp"]:
    assert len(asbCurrentInstructionArguments) == 1, \
        "Instruction on line 2 appears to have %d arguments instead of 1:\r\n%s" % \
        (len(asbCurrentInstructionArguments), b"\r\n".join(asbDiassemblyOutput));
    sbSourceArgument = asbCurrentInstructionArguments[0];
  else:
    assert len(asbCurrentInstructionArguments) == 2, \
        "Instruction on line 2 appears to have %d arguments instead of 2:\r\n%s" % \
        (len(asbCurrentInstructionArguments), b"\r\n".join(asbDiassemblyOutput));
    if sbCurrentInstructionName in [b"cmp"]:
      # This instruction will only affect flags, so we'll read 8 bits to use as flags from the poisoned values.
      # TODO: At some point, we may want to do this for other arithmatic operations as well.
      uPoisonFlagsValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, 8, uPointerSizedValue);
      asbFlags = [b"of", b"sf", b"zf", b"af", b"pf", b"cf"];
      duRegisterValue_by_sbName = dict([
        (asbFlags[uIndex], (uPoisonFlagsValue >> uIndex) & 1)
        for uIndex in range(len(asbFlags))
      ]);
      duRegisterValue_by_sbName[b"*ip"] = uNextInstructionAddress;
      if not oThread.fbSetRegisters(duRegisterValue_by_sbName):
#        print "@@@ set %s == False" % repr(duRegisterValue_by_sbName);
        return False;
      return True;
    (sbDestinationArgument, sbSourceArgument) = asbCurrentInstructionArguments;
    obDestinationArgumentPointerMatch = grbInstructionPointerArgumentTargetSize.match(sbDestinationArgument);
    if obDestinationArgumentPointerMatch:
      # We fake write AVs by ignoring the write and advancing the instruction pointer to the next instruction.
      # TODO: This does not alter flags like a normal instruction might!!!!
      if not oThread.fbSetRegister(b"*ip", uNextInstructionAddress):
#        print "@@@ set %s == False" % repr({"*ip": uNextInstructionAddress});
        return False;
      return True;
  obSourceArgumentPointerTargetSizeMatch = grbInstructionPointerArgumentTargetSize.match(sbSourceArgument);
  if obSourceArgumentPointerTargetSizeMatch is None:
    assert sbCurrentInstructionName in [b"call", b"jmp"], \
        "The source (%s) argument is expected to be a pointer for a %s instruction:\r\n%s" % \
        (sbSourceArgument, sbCurrentInstructionName, b"\r\n".join(asbDiassemblyOutput));
    # A call to an address taken from a register containing a bogus value would have resulted in an execute access
    # violation, after which we cannot continue.
#    print "@@@ sbSourceArgument == %s" % sbSourceArgument;
    return False;
  # We fake read AVs that read memory into a register by setting that register to a poisoned value and advancing
  # the instruction pointer to the next instruction.
  # This does not alter flags like a normal instruction!!!!
  sbDestinationRegister = sbDestinationArgument;
  uDestinationSizeInBits = gduSizeInBits_by_sbRegisterName[sbDestinationRegister];
  assert uDestinationSizeInBits is not None, \
      "Unrecognised `mov` instruction first/destination argument (expected register, got %s):\r\n%s" % \
      (sbDestinationRegister, b"\r\n".join(asbDiassemblyOutput));
  (sbSourcePointerTargetSize,) = obSourceArgumentPointerTargetSizeMatch.groups();
  uSourceSizeInBits = gduSizeInBits_by_sbPointerTargetSize[sbSourcePointerTargetSize];
  uPoisonValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, uSourceSizeInBits, uPointerSizedValue);
#    print "Faked read %d bits (0x%X) into %d bits %s" % (uSourceSize, uPoisonValue, uDestinationSizeInBits, sbDestinationRegister);
  duNewRegisterValues_by_sbName = {
    sbDestinationRegister: uPoisonValue,
    b"*ip": uNextInstructionAddress,
  };
  if not oThread.fbSetRegisters(duNewRegisterValues_by_sbName):
#    print "@@@ set %s == False" % repr(duNewRegisterValues_by_sbName);
    return False;
  return True;

