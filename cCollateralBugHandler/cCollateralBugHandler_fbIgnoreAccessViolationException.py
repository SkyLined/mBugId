import re;

# Any instructions in the below two arrays are handled. Anything else is not.
gasbInstructionsThatModifyFlags = [
    b"add", b"addsd",
    b"cmp", b"test",
    b"mulsd",
    b"sub", b"subsd",
    b"inc", b"dec",
];
gasbInstructionsThatModifyDestination = [
    b"add", b"addsd",
    b"mov", b"movzx", b"movsd",
    b"mulsd",
    b"sub", b"subsd",
    b"inc", b"dec",
];
gasbInstructionsThatReadDestination = [
    b"add", b"addsd",
    b"sub", b"subsd",
    b"inc", b"dec",
];
gasbInstructionsThatModifyInstructionPointer = [
  b"call", b"jmp",
];
gasbInstructionsThatCanBeHandled = set(
  gasbInstructionsThatModifyFlags
  + gasbInstructionsThatModifyDestination
  + gasbInstructionsThatReadDestination
  + gasbInstructionsThatModifyInstructionPointer
);

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

grbNumberArgument = re.compile(
  rb"^"
  rb"("                       # <<< either {
    rb"0x[0-9a-f]+"           #   "0x" hex digits
    rb"(?:"                   #    optional {
      rb"`[0-9a-f]+"          #      "`" hex digits
    rb")?"                    #    }
  rb"|"                       # } or {
    rb"[0-9a-f]+h"            #   hex digits "h"
  rb"|"                       # } or {
    rb"[0-9]+"                #   digits
  rb")"                       # } >>>
  rb"$"                       #
);

grbPointerArgumentTargetSize = re.compile(
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

def cCollateralBugHandler_fbIgnoreAccessViolationException(
  oSelf,
  oCdbWrapper,
  oProcess,
  oThread,
  sViolationTypeId,
  uViolationAddress,
  u0PointerSizedOriginalValue = None,
):
  if sViolationTypeId == "E":
    # The application is attempting to execute code at an address that does not point to executable memory; this cannot
    # be ignored.
#    print "@@@ sViolationTypeId == \"E\"";
    oCdbWrapper.fFireCallbacks(
      "Bug cannot be ignored", 
      "executing in un-executable memory is not handled"
    );
    return False;
  # See if we can fake execution of the current instruction, so we can continue the application as if it had been
  # executed without actually executing it.
  (sbInstructionPointerRegisterName, u0InstructionPointerValue) = oThread.ftxGetInstructionPointerRegisterNameAndValue();
  if u0InstructionPointerValue is None:
    # We cannot get the instruction pointer for this thread; it must be terminated and cannot be continued.
#    print "@@@ u0InstructionPointer == None";
    oCdbWrapper.fFireCallbacks(
      "Bug cannot be ignored", 
      "the instruction pointer for this thread could not be retrieved"
    );
    return False;
  uInstructionPointerValue = u0InstructionPointerValue;
  o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uInstructionPointerValue);
  if not o0VirtualAllocation or not o0VirtualAllocation.bExecutable:
    # This can happen if a call/return sets the instruction pointer to a corrupted value; it may point to a region that
    # is not allocated, or contains non-executable data. (e.g. a poisoned value)
#    print "@@@ o0VirtualAllocation.bExecutable == False";
    oCdbWrapper.fFireCallbacks(
      "Bug cannot be ignored", 
      "executing in un-executable memory is not handled"
    );
    return False; # This memory is not executable: we cannot continue execution.
  o0CurrentInstruction = oProcess.fo0GetInstructionForAddress(
    uAddress = uInstructionPointerValue,
  );
  if o0CurrentInstruction is None:
    # The instruction pointer does not point to valid memory.
    oCdbWrapper.fFireCallbacks(
      "Bug cannot be ignored", 
      "the disassembly of the code being executed could not be retrieved"
    );
    return False;
  oCurrentInstruction = o0CurrentInstruction;
  # Check if we can handle the instruction.
  if oCurrentInstruction.sbName not in gasbInstructionsThatCanBeHandled:
    oCdbWrapper.fFireCallbacks(
      "Bug cannot be ignored", 
      "the instruction %s is not currently handled" % str(oCurrentInstruction),
    );
    return False;

  uNextInstructionAddress = oCurrentInstruction.uAddress + oCurrentInstruction.uSize;

  # Decide what registers to modify (if any) and record what actions this represents.
  duNewRegisterValue_by_sbName = {};
  asActions = [];
  ############################################################################
  # Handle jumps/call instructions and advance to next instruction for others
  if oCurrentInstruction.sbName in gasbInstructionsThatModifyInstructionPointer:
    if not oSelf.fbPoisonRegister(
      oProcess = oProcess,
      oThread = oThread,
      sInstruction = str(oCurrentInstruction),
      duPoisonedRegisterValue_by_sbName = duNewRegisterValue_by_sbName,
      u0PointerSizedOriginalValue = u0PointerSizedOriginalValue,
      sbRegisterName = sbInstructionPointerRegisterName,
      uSizeInBits = gduSizeInBits_by_sbRegisterName[sbInstructionPointerRegisterName],
    ):
      return False;
    asActions.append("%s register set to 0x%X" % (
      str(sbInstructionPointerRegisterName, "ascii", "strict"),
      duNewRegisterValue_by_sbName[sbInstructionPointerRegisterName],
    ));
  else:
    duNewRegisterValue_by_sbName[sbInstructionPointerRegisterName] = uNextInstructionAddress;
  ############################################################################
  # Handle instructions that modify flags
  if oCurrentInstruction.sbName in gasbInstructionsThatModifyFlags:
    if not oSelf.fbPoisonFlags(
      oCdbWrapper = oCdbWrapper,
      oProcess = oProcess,
      oThread = oThread,
      sInstruction = str(oCurrentInstruction),
      duPoisonedRegisterValue_by_sbName = duNewRegisterValue_by_sbName,
      u0PointerSizedOriginalValue = u0PointerSizedOriginalValue,
    ):
      return False;
    asActions.append("flags set");

  ############################################################################
  # Handle instructions that modify a destination register or memory.
  if oCurrentInstruction.sbName in gasbInstructionsThatModifyDestination:
    if len(oCurrentInstruction.tsbArguments) == 1:
      sbDestinationArgument = sbSourceArgument = oCurrentInstruction.tsbArguments[0];
    elif len(oCurrentInstruction.tsbArguments) == 2:
      (sbDestinationArgument, sbSourceArgument) = oCurrentInstruction.tsbArguments;
    else:
      oCdbWrapper.fFireCallbacks(
        "Bug cannot be ignored", 
        "instruction %s has too many arguments" % (
          str(oCurrentInstruction),
        ),
      );
      return False;
    # <helper function>
    def fu0GetSizeInBitsOfMemoryPointerArgument(sArgumentType, sbArgument):
      ob0ArgumentTargetSizeMatch = grbPointerArgumentTargetSize.match(sbArgument);
      if not ob0ArgumentTargetSizeMatch:
        oCdbWrapper.fFireCallbacks(
          "Bug cannot be ignored", 
          "instruction %s %s argument %s cannot be decoded" % (
            str(oCurrentInstruction),
            sArgumentType,
            str(sbArgument, "ascii", "strict"),
          ),
        );
        return None;
      (sbSourcePointerTargetSize,) = ob0ArgumentTargetSizeMatch.groups();
      return gduSizeInBits_by_sbPointerTargetSize[sbSourcePointerTargetSize];
    # </helper function>
    # Process destination argument
    u0DestinationArgumentPointerSizeInBits = None;
    if sbDestinationArgument in gduSizeInBits_by_sbRegisterName:
      sDestination = "register %s" % (
        str(sbSourceArgument, "ascii", "strict"),
      );
    else:
      u0DestinationArgumentPointerSizeInBits = fu0GetSizeInBitsOfMemoryPointerArgument("destination", sbDestinationArgument);
      if u0DestinationArgumentPointerSizeInBits is None:
        return False;
      sDestination = "memory at %s (0x%X)" % (
        str(sbSourceArgument, "ascii", "strict"),
        uViolationAddress,
      );
    # Process source argument
    u0SourceArgumentPointerSizeInBits = None;
    u0SourceValue = None;
    if sbSourceArgument in gduSizeInBits_by_sbRegisterName:
      u0SourceValue = oThread.fu0GetRegister(sbSourceArgument);
      if u0SourceValue is None:
        oCdbWrapper.fFireCallbacks(
          "Bug cannot be ignored", 
          "Cannot get value of source register %s" % (
            str(sbSourceArgument, "ascii", "strict"),
          ),
        );
        return False;
      sSource = "register %s (0x%X)" % (
        str(sbSourceArgument, "ascii", "strict"),
        u0SourceValue,
      );
    elif grbNumberArgument.match(sbSourceArgument):
      if sbSourceArgument.startswith(b"0x"):
        u0SourceValue = int(sbSourceArgument[2:].replace(b"`", b""), 16);
        sSource = "0x%X" % u0SourceValue;
      elif sbSourceArgument.endswith(b"h"):
        u0SourceValue = int(sbSourceArgument[:1], 16);
        sSource = "0x%X" % u0SourceValue;
      else:
        u0SourceValue = int(sbSourceArgument);
        sSource = "%d" % u0SourceValue;
    else:
      u0SourceArgumentPointerSizeInBits = fu0GetSizeInBitsOfMemoryPointerArgument("source", sbSourceArgument);
      if u0SourceArgumentPointerSizeInBits is None:
        return False;
      sSource = "memory at %s (0x%X)" % (
        str(sbSourceArgument, "ascii", "strict"),
        uViolationAddress,
      );
    if oCurrentInstruction.sbName in gasbInstructionsThatReadDestination:
      if sSource != sDestination:
        sSource = "%s and %s" % (sDestination, sSource);
    bSourceCausedBug = u0SourceArgumentPointerSizeInBits is not None;
    bDestinationCausedBug = u0DestinationArgumentPointerSizeInBits is not None;
    if bSourceCausedBug and bDestinationCausedBug:
      ############################################################################
      # Handle instructions that attempted to modify invalid memory.
      
      # This is either a single argument instruction like inc, where source == destination
      # or an instruction that reads from and writes to memory. The last case means that
      # either the source, or the destination, or both could have cause the AV. That is a
      # situation that we currently do not handle:
      if sbDestinationArgument != sbSourceArgument:
        oCdbWrapper.fFireCallbacks(
          "Bug cannot be ignored", 
          "Source and destination in %s instruction are two different pointers" % (
            str(oCurrentInstruction),
          ),
        );
        return False;
      asActions.append("ignored modifying memory at %s" % (
        sDestination,
      ));
    elif bDestinationCausedBug:
      ############################################################################
      # Handle instructions that attempted to overwrite invalid memory.
      uDestinationArgumentPointerSizeInBits = u0DestinationArgumentPointerSizeInBits;
      # The source must be a register or constant, so we can determine the value
      # that was attempted to be written and show it:
      if u0SourceValue is None:
        oCdbWrapper.fFireCallbacks(
          "Bug cannot be ignored", 
          "cannot determine %s value" % sSource,
        );
        return False;
      # We may only write part of the source value, so truncate it appropriately:
      uWrittenValue = u0SourceValue & ((1 << uDestinationArgumentPointerSizeInBits) - 1);
      asActions.append("ignored writing 0x%X to %d bits of memory at %s" % (
        uWrittenValue,
        uDestinationArgumentPointerSizeInBits,
        sDestination,
      ));
    elif bSourceCausedBug:
      ############################################################################
      # Handle instructions that attempted to read invalid memory.
      # * Poison the destination register.
      # TODO: Do proper zero-ing, sign-extending, etc... based on instruction
      uSourceArgumentPointerSizeInBits = u0SourceArgumentPointerSizeInBits;
      if u0PointerSizedOriginalValue is not None:
        # We may only read part of the source, so truncate the value appropriately
        u0PointerSizedOriginalValue &= ((1 << uSourceArgumentPointerSizeInBits) - 1);
      oSelf.fbPoisonRegister(
        oProcess = oProcess,
        oThread = oThread,
        sInstruction = str(oCurrentInstruction),
        duPoisonedRegisterValue_by_sbName = duNewRegisterValue_by_sbName,
        u0PointerSizedOriginalValue = u0PointerSizedOriginalValue,
        sbRegisterName = sbDestinationArgument,
        uSizeInBits = uSourceArgumentPointerSizeInBits,
      )
      asActions.append("set register %s = 0x%X to fake reading %d bits of memory from %s" % (
        str(sbDestinationArgument, "ascii", "strict"),
        duNewRegisterValue_by_sbName[sbDestinationArgument],
        uSourceArgumentPointerSizeInBits,
        sSource,
      ));
    else:
      oCdbWrapper.fFireCallbacks(
        "Bug cannot be ignored", 
        "Neither source nor destination in %s instruction appear to have caused this issue" % (
          str(oCurrentInstruction),
        ),
      );
      return False;
  if oCurrentInstruction.sbName == b"call":
    (sbStackPointerRegisterName, u0StackPointerValue) = oThread.ftxGetStackPointerRegisterNameAndValue();
    if u0StackPointerValue is None:
      oCdbWrapper.fFireCallbacks(
        "Bug cannot be ignored", 
        "The value of the %s register cannot be determined" % repr(sbStackPointerRegisterName)[1:],
      );
      return False;
    duNewRegisterValue_by_sbName[sbStackPointerRegisterName] = u0StackPointerValue - oProcess.uPointerSize;
    # TODO: write return address to Stack!!!
    asActions.append("stack pointer %s decreased, BUT NO RETURN ADDRESS WRITTEN!!" % (
      str(sbStackPointerRegisterName, "ascii", "strict"),
    ));
  if duNewRegisterValue_by_sbName and not oThread.fbSetRegisters(duNewRegisterValue_by_sbName):
#    print "@@@ set %s == False" % repr(duNewRegisterValues_by_sbName);
    oCdbWrapper.fFireCallbacks(
      "Bug cannot be ignored", 
      "cannot set registers (%s)" % ", ".join(
          str(sbRegisterName, "ascii", "strict")
          for sbRegisterName in duNewRegisterValue_by_sbName
      ),
    );
    return False;
  oCdbWrapper.fFireCallbacks("Bug ignored", str(oCurrentInstruction), asActions);
  return True;

