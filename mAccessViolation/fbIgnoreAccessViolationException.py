import re;

gduSizeInBits_by_sRegisterName = {
  "rax": 64,  "eax": 32,   "ax": 16, "ah": 8,  "al": 8,
  "rbx": 64,  "ebx": 32,   "bx": 16, "bh": 8,  "bl": 8,
  "rcx": 64,  "ecx": 32,   "cx": 16, "ch": 8,  "cl": 8,
  "rdx": 64,  "edx": 32,   "dx": 16, "dh": 8,  "dl": 8,
  "rsi": 64,  "esi": 32,   "si": 16,          "sil": 8,
  "rdi": 64,  "edi": 32,   "di": 16,          "dil": 8,
  "rbp": 64,  "ebp": 32,   "bp": 16,          "bpl": 8,
  "rsp": 64,  "esp": 32,   "sp": 16,          "spl": 8,
  "rip": 64,  "eip": 32,   "ip": 16,
   "r8": 64,  "r8d": 32,  "r8w": 16,          "r8b": 8,
   "r9": 64,  "r9d": 32,  "r9w": 16,          "r9b": 8,
  "r10": 64, "r10d": 32, "r10w": 16,         "r10b": 8,
  "r11": 64, "r11d": 32, "r11w": 16,         "r11b": 8,
  "r12": 64, "r12d": 32, "r12w": 16,         "r12b": 8,
  "r13": 64, "r13d": 32, "r13w": 16,         "r13b": 8,
  "r14": 64, "r14d": 32, "r14w": 16,         "r14b": 8,
  "r15": 64, "r15d": 32, "r15w": 16,         "r15b": 8,
    "mm0":  64,   "mm1":  64,   "mm2":  64,   "mm3":  64,   "mm4":  64,   "mm5":  64,  "mm6":   64,  "mm7":   64,
   "xmm0": 128,  "xmm1": 128,  "xmm2": 128,  "xmm3": 128,  "xmm4": 128,  "xmm5": 128,  "xmm6": 128,  "xmm7": 128,
   "xmm8": 128,  "xmm9": 128, "xmm10": 128, "xmm11": 128, "xmm12": 128, "xmm13": 128, "xmm14": 128, "xmm15": 128,
# No support for xmm16-31 or ymm in mWindowsAPI yet, as there is no documentation on where these are stored in the
# CONTEXT struct used by Get-/SetThreadContext.
#  "xmm16": 128, "xmm17": 128, "xmm18": 128, "xmm19": 128, "xmm20": 128, "xmm21": 128, "xmm22": 128, "xmm23": 128,
#  "xmm24": 128, "xmm25": 128, "xmm26": 128, "xmm27": 128, "xmm28": 128, "xmm29": 128, "xmm30": 128, "xmm31": 128, 
#   "ymm0": 256,  "ymm1": 256,  "ymm2": 256,  "ymm3": 256,  "ymm4": 256,  "ymm5": 256,  "ymm6": 256,  "ymm7": 256,
#   "ymm8": 256,  "ymm9": 256, "ymm10": 256, "ymm11": 256, "ymm12": 256, "ymm13": 256, "ymm14": 256, "ymm15": 256,
#  "ymm16": 256, "ymm17": 256, "ymm18": 256, "ymm19": 256, "ymm20": 256, "ymm21": 256, "ymm22": 256, "ymm23": 256,
#  "ymm24": 256, "ymm25": 256, "ymm26": 256, "ymm27": 256, "ymm28": 256, "ymm29": 256, "ymm30": 256, "ymm31": 256, 
};
gduSizeInBits_by_sPointerType = {
  # No support for ymm yet.
  "byte": 8, "word": 16, "dword": 32, "qword": 64, "mmword": 64, "xmmword": 128, # "ymmword": 256,
};

def fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess, oThread, sViolationTypeId, uPointerSizedValue = None):
  if sViolationTypeId == "E":
    # The application is attempting to execute code at an address that does not point to executable memory; this cannot
    # be ignored.
#    print "@@@ sViolationTypeId == \"E\"";
    return False;
  # See if we can fake execution of the current instruction, so we can continue the application as if it had been
  # executed without actually executing it.
  sInstructionPointerRegister = {"x86": "eip", "x64": "rip"}[oProcess.sISA];
  u0InstructionPointer = oThread.fu0GetRegister("*ip");
  if u0InstructionPointer is None:
    # We cannot get the instruction pointer for this thread; it must be terminated and cannot be continued.
#    print "@@@ u0InstructionPointer == None";
    return False;
  uInstructionPointer = u0InstructionPointer;
  oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uInstructionPointer);
  if not oVirtualAllocation.bExecutable:
    # This can happen if a call/return sets the instruction pointer to a corrupted value; it may point to a region that
    # is not allocated, or contains non-executable data. (e.g. a poisoned value)
#    print "@@@ oVirtualAllocation.bExecutable == False";
    return False; # This memory is not executable: we cannot continue execution.
  asDiassemblyOutput = oProcess.fasExecuteCdbCommand(
    sCommand = "u 0x%X L2" % uInstructionPointer, 
    sComment = "Get information about the instruction that caused the AV",
  );
  if len(asDiassemblyOutput) == 0:
    # The instruction pointer does not point to valid memory.
#    print "@@@ asDiassemblyOutput == []";
    return False;
  assert len(asDiassemblyOutput) == 3, \
      "Expected 3 lines of disassembly, got %d:\r\n%s" % (len(asDiassemblyOutput), "\r\n".join(asDiassemblyOutput));
  (sSymbol, sCurrentInstruction, sNextInstruction) = asDiassemblyOutput;
  # Grab info from current instruction (name and arguments):
  oCurrentInstructionMatch = re.match(r"^[0-9`a-f]+\s+[0-9`a-f]+\s+(\w+)(?:\s+(.*))?$", sCurrentInstruction, re.I);
  assert oCurrentInstructionMatch, \
      "Unrecognised diassembly output second line:\r\n%s" % "\r\n".join(asDiassemblyOutput);
  (sCurrentInstructionName, sCurrentInstructionArguments) = oCurrentInstructionMatch.groups();
  if sCurrentInstructionName not in ["add", "addsd", "call", "cmp", "jmp", "mov", "movzx", "movsd", "mulsd", "sub", "subsd"]:
#    print "Cannot handle instruction %s:\r\n%s" % (repr(sCurrentInstructionName), "\r\n".join(asDiassemblyOutput));
#    print "@@@ sCurrentInstructionName == %s" % repr(sCurrentInstructionName);
    return False;
  # Grab info from next instruction (it's starting address):
  oNextInstructionMatch = re.match(r"^([0-9`a-f]+)\s+[0-9`a-f]+\s+\w+(?:\s+.*)?$", sNextInstruction, re.I);
  assert oNextInstructionMatch, \
      "Unrecognised diassembly output third line:\r\n%s" % "\r\n".join(asDiassemblyOutput);
  (sNextInstructionAddress,) = oNextInstructionMatch.groups();
  uNextInstructionAddress = long(sNextInstructionAddress.replace("`", ""), 16);
  # We do not care about the difference between these operations; for writes, we simply discard the value. For reads
  # we assume that we have full control over the memory at the specified address, and thus full control over the
  # result stored in the register, so we just fake reading a poisoned value.
  asCurrentInstructionArguments = sCurrentInstructionArguments.split(",");
  if sCurrentInstructionName in ["call", "jmp"]:
    assert len(asCurrentInstructionArguments) == 1, \
        "Instruction on line 2 appears to have %d arguments instead of 1:\r\n%s" % \
        (len(asCurrentInstructionArguments), "\r\n".join(asDiassemblyOutput));
    sSourceArgument = asCurrentInstructionArguments[0];
  else:
    assert len(asCurrentInstructionArguments) == 2, \
        "Instruction on line 2 appears to have %d arguments instead of 2:\r\n%s" % \
        (len(asCurrentInstructionArguments), "\r\n".join(asDiassemblyOutput));
    if sCurrentInstructionName in ["cmp"]:
      # This instruction will only affect flags, so we'll read 8 bits to use as flags from the poisoned values.
      # TODO: At some point, we may want to do this for other arithmatic operations as well.
      uPoisonFlagsValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, 8, uPointerSizedValue);
      asFlags = ["of", "sf", "zf", "af", "pf", "cf"];
      duRegisterValue_by_sName = dict([
        (asFlags[uIndex], (uPoisonFlagsValue >> uIndex) & 1)
        for uIndex in xrange(len(asFlags))
      ]);
      duRegisterValue_by_sName["*ip"] = uNextInstructionAddress;
      if not oThread.fbSetRegisters(duRegisterValue_by_sName):
#        print "@@@ set %s == False" % repr(duRegisterValue_by_sName);
        return False;
      return True;
    (sDestinationArgument, sSourceArgument) = asCurrentInstructionArguments;
    oDestinationArgumentPointerMatch = re.match("^(byte|(?:d|q|[xy]?(mm))?word) ptr \[.*\]$", sDestinationArgument);
    if oDestinationArgumentPointerMatch:
      # We fake write AVs by ignoring the write and advancing the instruction pointer to the next instruction.
      # TODO: This does not alter flags like a normal instruction might!!!!
      if not oThread.fbSetRegister("*ip", uNextInstructionAddress):
#        print "@@@ set %s == False" % repr({"*ip": uNextInstructionAddress});
        return False;
      return True;
  oSourceArgumentPointerMatch = re.match("^(byte|(?:d|q|[xy]?mm)?word) ptr \[.*\]$", sSourceArgument);
  if oSourceArgumentPointerMatch is None:
    assert sCurrentInstructionName in ["call", "jmp"], \
        "The source (%s) argument is expected to be a pointer for a %s instruction:\r\n%s" % \
        (sSourceArgument, sCurrentInstructionName, "\r\n".join(asDiassemblyOutput));
    # A call to an address taken from a register containing a bogus value would have resulted in an execute access
    # violation, after which we cannot continue.
#    print "@@@ sSourceArgument == %s" % sSourceArgument;
    return False;
  # We fake read AVs that read memory into a register by setting that register to a poisoned value and advancing
  # the instruction pointer to the next instruction.
  # This does not alter flags like a normal instruction!!!!
  sDestinationRegister = sDestinationArgument;
  uDestinationSizeInBits = gduSizeInBits_by_sRegisterName[sDestinationRegister];
  assert uDestinationSizeInBits is not None, \
      "Unrecognised `mov` instruction first/destination argument (expected register, got %s):\r\n%s" % \
      (sDestinationRegister, "\r\n".join(asDiassemblyOutput));
  (sSourcePointerType,) = oSourceArgumentPointerMatch.groups();
  uSourceSizeInBits = gduSizeInBits_by_sPointerType[sSourcePointerType];
  uPoisonValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, uSourceSizeInBits, uPointerSizedValue);
#    print "Faked read %d bits (0x%X) into %d bits %s" % (uSourceSize, uPoisonValue, uDestinationSizeInBits, sDestinationRegister);
  duNewRegisterValues_by_sName = {
    sDestinationRegister: uPoisonValue,
    "*ip": uNextInstructionAddress,
  };
  if not oThread.fbSetRegisters(duNewRegisterValues_by_sName):
#    print "@@@ set %s == False" % repr(duNewRegisterValues_by_sName);
    return False;
  return True;

