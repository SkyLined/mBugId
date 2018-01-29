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
  "xmm16": 128, "xmm17": 128, "xmm18": 128, "xmm19": 128, "xmm20": 128, "xmm21": 128, "xmm22": 128, "xmm23": 128,
  "xmm24": 128, "xmm25": 128, "xmm26": 128, "xmm27": 128, "xmm28": 128, "xmm29": 128, "xmm30": 128, "xmm31": 128, 
   "ymm0": 256,  "ymm1": 256,  "ymm2": 256,  "ymm3": 256,  "ymm4": 256,  "ymm5": 256,  "ymm6": 256,  "ymm7": 256,
   "ymm8": 256,  "ymm9": 256, "ymm10": 256, "ymm11": 256, "ymm12": 256, "ymm13": 256, "ymm14": 256, "ymm15": 256,
  "ymm16": 256, "ymm17": 256, "ymm18": 256, "ymm19": 256, "ymm20": 256, "ymm21": 256, "ymm22": 256, "ymm23": 256,
  "ymm24": 256, "ymm25": 256, "ymm26": 256, "ymm27": 256, "ymm28": 256, "ymm29": 256, "ymm30": 256, "ymm31": 256, 
};
gduSizeInBits_by_sPointerType = {
  "byte": 8, "word": 16, "dword": 32, "qword": 64, "mmword": 64, "xmmword": 128, "ymmword": 256,
};

def fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, uProcessId, sViolationTypeId, uPointerSizedValue = None):
  # I could just pass the oProcess, as there is no code execution between when the exception handler was set and called,
  # but if that changes in the future, this.
  oProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
  # See if we can fake execution of the current instruction, so we can continue the application as if it had been
  # executed without actually executing it.
  uInstructionPointer = oProcess.fuGetValueForRegister("$ip", "Get current instruction pointer");
  oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uInstructionPointer);
  if not oVirtualAllocation.bExecutable:
    return False; # This memory is not executable: we cannot continue execution.
  asUnassembleOutput = oProcess.fasExecuteCdbCommand(
    sCommand = "u 0x%X L2" % uInstructionPointer, 
    sComment = "Get information about the instruction that caused the AV",
  );
  if len(asUnassembleOutput) == 0:
    # The instruction pointer does not point to valid memory.
    return False;
  oCurrentInstructionMatch = len(asUnassembleOutput) == 3 and \
      re.match(r"^[0-9`a-f]+\s+[0-9`a-f]+\s+(\w+)(?:\s+(.*))?$", asUnassembleOutput[1], re.I);
  oNextInstructionMatch = len(asUnassembleOutput) == 3 and \
      re.match(r"^([0-9`a-f]+)\s+[0-9`a-f]+\s+\w+(?:\s+.*)?$", asUnassembleOutput[2], re.I);
  assert oCurrentInstructionMatch, \
      "Unrecognised unassemble output second line:\r\n%s" % "\r\n".join(asUnassembleOutput);
  assert oNextInstructionMatch, \
      "Unrecognised unassemble output third line:\r\n%s" % "\r\n".join(asUnassembleOutput);
  (sCurrentInstructionName, sCurrentInstructionArguments) = oCurrentInstructionMatch.groups();
  (sNextInstructionAddress,) = oNextInstructionMatch.groups();
  uNextInstructionAddress = long(sNextInstructionAddress.replace("`", ""), 16);
  if sCurrentInstructionName in ["add", "addsd", "mov", "movzx", "movsd", "mulsd", "sub", "subsd"]:
    # We do not care about the difference between these operations; for writes, we simply discard the value. For reads
    # we assume that we have full control over the memory at the specified address, and thus full control over the
    # result stored in the register, so we just fake reading a poisoned value.
    asCurrentInstructionArguments = sCurrentInstructionArguments.split(",");
    assert len(asCurrentInstructionArguments) == 2, \
        "Instruction on line 2 appears to have %d arguments instead of 2:\r\n%s" % \
        (len(asCurrentInstructionArguments), "\r\n".join(asUnassembleOutput));
    sInstructionPointerRegister = {"x86": "eip", "x64": "rip"}[oProcess.sISA];
    if sViolationTypeId == "R":
      # We fake read AVs that read memory into a register by setting that register to a poisoned value and advancing
      # the instruction pointer to the next instruction.
      sDestinationRegister = asCurrentInstructionArguments[0];
      uDestinationSizeInBits = gduSizeInBits_by_sRegisterName[sDestinationRegister];
      assert uDestinationSizeInBits is not None, \
          "Unrecognised `mov` instruction first/destination argument (expected register, got %s):\r\n%s" % \
          (sDestinationRegister, "\r\n".join(asUnassembleOutput));
      oSourceArgumentMatch = re.match("^(byte|(?:d|q|[xy]?(mm))?word) ptr \[.*\]$", asCurrentInstructionArguments[1]);
      assert oSourceArgumentMatch, \
          "Unrecognized `mov` instruction second/source argument (expected `... ptr [...]`, got %s):\r\n%s" % \
          (asCurrentInstructionArguments[1], "\r\n".join(asUnassembleOutput));
      sPointerType, bIsMMPointer = oSourceArgumentMatch.groups();
      uSourceSizeInBits = gduSizeInBits_by_sPointerType[sPointerType];
      if not bIsMMPointer:
        uPoisonValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, uSourceSizeInBits, uPointerSizedValue);
#        print "Faked read %d bits (0x%X) into %d bits %s" % (uSourceSize, uPoisonValue, uDestinationSizeInBits, sDestinationRegister);
        asSpoofInstructionOutput = oProcess.fasExecuteCdbCommand(
          sCommand = "r @%s=0x%X,@%s=0x%X,@%s,@%s;" % (
            sDestinationRegister, uPoisonValue,
            sInstructionPointerRegister, uNextInstructionAddress,
            sDestinationRegister, sInstructionPointerRegister,
          ),
          sComment = "Fake and skip instruction that caused the read AV",
        );
      else:
        # This is a bit more involved, as we can only set entire MM registers using 4 floating point numbers and we
        # want to set it to one or more pointer sized integers, which may mean we only want to set part of the register.
        if uSourceSizeInBits != uDestinationSizeInBits:
          # We want to write only part of the register: read the current value so we can preserve part of it.
          asGetDestinationBytesOutput = oProcess.fasExecuteCdbCommand(
            sCommand = "r @%s:%dub;" % (sDestinationRegister, uDestinationSizeInBits / 8),
            sComment = "Get current value of register",
          );
#          print "asGetDestinationBytesOutput: %s" % repr(asGetDestinationBytesOutput);
          assert len(asGetDestinationBytesOutput) == 1 and asGetDestinationBytesOutput[0].startswith("%s=" % sDestinationRegister), \
              "Unexpected register value output:\r\n%s" % "\r\n".join(asGetDestinationBytesOutput);
          auDestinationRegisterBytes = [long(s, 16) for s in asGetDestinationBytesOutput[0].split("=", 1)[1].split(" ") if s];
          auDestinationRegisterBytes.reverse();
        else:
          # Everything will be overwritten.
          auDestinationRegisterBytes = [0 for x in xrange(uDestinationSizeInBits / 8)];
#        print "auDestinationRegisterBytes: %s" % repr(auDestinationRegisterBytes);
        # We will fake read as many pointer sized values from the collateral poison value queue as will fit in the
        # source value.
        uPointerSizeInBits = oProcess.uPointerSize * 8;
        uSourceSizeInPointers = uSourceSizeInBits / uPointerSizeInBits;
        uIndex = 0;
        for x in xrange(uSourceSizeInPointers):
          uPoisonValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, uPointerSizeInBits, uPointerSizedValue);
          # The bytes in this poison value are written to the destination register buffer.
          for y in xrange(uPointerSizeInBits / 8):
            auDestinationRegisterBytes[uIndex] = uPoisonValue & 0xFF;
            uPoisonValue >>= 8;
            uIndex += 1;
#        print "auDestinationRegisterBytes: %s" % repr(auDestinationRegisterBytes);
        # We now know the bytes we want in the destination register, but we can only set it as 4 float values. So we
        # will convert these bytes to four floats:
        sDestinationRegisterBytes = "".join([chr(uByte) for uByte in auDestinationRegisterBytes]);
        uFloatSizeInBits = uDestinationSizeInBits / 4;
        anDestinationRegisterFloats = struct.unpack(">%s" % ({32: "f", 64: "d"}[uFloatSizeInBits] * 4), sDestinationRegisterBytes);
#        print "anDestinationRegisterFloats: %s" % repr(anDestinationRegisterFloats);
        sDestinationRegisterFloats = " ".join(["%f" % nFloat for nFloat in anDestinationRegisterFloats]);
        # Overwrite the register to fake a read instruction and update the instruction pointer to the next instruction.
        asSpoofInstructionOutput = oProcess.fasExecuteCdbCommand(
          sCommand = "r @%s=%s,@%s=0x%X,@%s,@%s;" % (
            sDestinationRegister, sDestinationRegisterFloats,
            sInstructionPointerRegister, uNextInstructionAddress,
            sDestinationRegister, sInstructionPointerRegister,
          ),
          sComment = "Fake and skip instruction that caused the read AV",
        );
#        print "asSpoofInstructionOutput: %s" % repr(asSpoofInstructionOutput);
    else:
      # We fake write AVs that write a register to memory by advancing the instruction pointer to the next
      # instruction.
      asSpoofInstructionOutput = oProcess.fasExecuteCdbCommand(
        sCommand = "r @%s=0x%X;" % (sInstructionPointerRegister, uNextInstructionAddress),
        sComment = "Skip instruction that caused the write AV",
      );
    return True;
  else:
    return False;
