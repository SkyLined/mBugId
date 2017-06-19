import re;
from cModule import cModule;
from cStackFrame import cStackFrame;
from dxConfig import dxConfig;

srIgnoredWarningsAndErrors = r"^(?:%s)$" % "|".join([
  # These warnings and errors are ignored:
  r"Unable to read dynamic function table list head",
]);

class cStack(object):
  def __init__(oStack):
    oStack.aoFrames = [];
    oStack.bPartialStack = True;
  
  def foCreateAndAddStackFrame(oStack,
    uIndex,
    sCdbSymbolOrAddress,
    uInstructionPointer, uReturnAddress,
    uAddress,
    sUnloadedModuleFileName,
    oModule, uModuleOffset,
    oFunction, iFunctionOffset,
    sSourceFilePath = None, uSourceFileLineNumber = None,
  ):
    # frames must be created in order:
    assert uIndex == len(oStack.aoFrames), \
        "Unexpected frame index %d vs %d" % (uIndex, len(oStack.aoFrames));
    uMaxStackFramesCount = dxConfig["uMaxStackFramesCount"];
    oStackFrame = cStackFrame(
      oStack,
      uIndex,
      sCdbSymbolOrAddress,
      uInstructionPointer, uReturnAddress,
      uAddress,
      sUnloadedModuleFileName,
      oModule, uModuleOffset, 
      oFunction, iFunctionOffset,
      sSourceFilePath, uSourceFileLineNumber,
    );
    oStack.aoFrames.append(oStackFrame);
    return oStackFrame;
  
  def fbTopFramesMatchSymbols(oStack, asSymbols, sHideWithReason = None):
    uFrameIndex = 0;
    while uFrameIndex < len(oStack.aoFrames) and (oStack.aoFrames[uFrameIndex].sIsHiddenBecause is not None):
      uFrameIndex += 1;
    if len(asSymbols) > len(oStack.aoFrames) - uFrameIndex:
      return False; # There are not enough non-hidden frames to match this translation
    uStartFrameIndex = uFrameIndex;
    for sSymbol in asSymbols:
      if not oStack.aoFrames[uFrameIndex].fbMatchesSymbol(sSymbol):
        return False;
      uFrameIndex += 1;
    if sHideWithReason is not None:
      uEndFrameIndex = uFrameIndex;
      for uFrameIndex in xrange(uStartFrameIndex, uEndFrameIndex):
        oStack.aoFrames[uFrameIndex].sIsHiddenBecause = sHideWithReason;
    return True;
  
  @classmethod
  def foCreateFromAddress(cStack, oProcess, pAddress, uSize):
    oCdbWrapper = oProcess.oCdbWrapper;
    # Create the stack object
    oProcess.fSelectInCdb();
    uStackFramesCount = min(dxConfig["uMaxStackFramesCount"], uSize);
    asStack = oCdbWrapper.fasGetStack("dps 0x%X L0x%X" % (pAddress, uStackFramesCount + 1));
    if not asStack: return None;
    oStack = cStack(asStack);
    # Here are some lines you might expect to parse:
    # |TODO put something here...
    uFrameIndex = 0;
    uInstructionPointer = None; # Unknown for first frame.
    for sLine in asStack:
      if uFrameIndex == uStackFramesCount:
        break;
      oMatch = re.match(r"^\s*%s\s*$" % (
        r"[0-9A-F`]+" r"\s+"                    #   stack_address whitespace
        r"([0-9A-F`]+)" r"\s+"                  #   (return_address) whitespace
        r"(.+?)"                                # (Symbol or address)
        r"(?: \[(.+) @ (\d+)\])?"               # [ "[" (source_file_path) " @ " (line_number) "]" ]
      ), sLine, re.I);
      assert oMatch, "Unknown stack output: %s" % sLine;
      sReturnAddress, sCdbSymbolOrAddress, sSourceFilePath, sSourceFileLineNumber = oMatch.groups();
      (
        uAddress,
        sUnloadedModuleFileName, oModule, uModuleOffset,
        oFunction, iFunctionOffset
      ) = oProcess.ftxSplitSymbolOrAddress(sCdbSymbolOrAddress);
      uSourceFileLineNumber = sSourceFileLineNumber and long(sSourceFileLineNumber);
      uReturnAddress = sReturnAddress and long(sReturnAddress.replace("`", ""), 16);
      oStackFrame = oStack.foCreateAndAddStackFrame(
        uIndex = uFrameIndex,
        sCdbSymbolOrAddress = sCdbSymbolOrAddress, 
        uInstructionPointer = uInstructionPointer,
        uReturnAddress = uReturnAddress,
        uAddress = uAddress, 
        sUnloadedModuleFileName = sUnloadedModuleFileName,
        oModule = oModule, uModuleOffset = uModuleOffset, 
        oFunction = oFunction, iFunctionOffset = iFunctionOffset,
        sSourceFilePath = sSourceFilePath, uSourceFileLineNumber = uSourceFileLineNumber,
      );
      if uReturnAddress:
        # Last frame's return address is next frame's instruction pointer.
        uInstructionPointer = uReturnAddress;
      uFrameIndex += 1;
    oStack.bPartialStack = uFrameIndex == uStackFramesCount;
    return oStack;
  
  @classmethod
  def foCreate(cStack, oProcess, uStackFramesCount):
    oCdbWrapper = oProcess.oCdbWrapper;
    oProcess.fSelectInCdb();
    # Get information on all modules in the current process
    # First frame's instruction pointer is exactly that:
    uInstructionPointer = oCdbWrapper.fuGetValue("@$ip", "Get instruction pointer");
    # Cache symbols that are called based on the return address after the call.
    dCache_toCallModuleAndFunction_by_uReturnAddress = {};
    for uTryCount in xrange(dxConfig["uMaxSymbolLoadingRetries"] + 1):
      asStackOutput = oCdbWrapper.fasSendCommandAndReadOutput("kn 0x%X; $$ Get stack" % (uStackFramesCount + 1));
      # Here are some lines you might expect to parse:
      # |00 (Inline) -------- chrome_child!WTF::RawPtr<blink::Document>::operator*+0x11
      # |03 0082ec08 603e2568 chrome_child!blink::XMLDocumentParser::startElementNs+0x105
      # |33 0082fb50 0030d4ba chrome!wWinMain+0xaa
      # |23 0a8cc578 66629c9b 0x66cf592a
      # |13 0a8c9cc8 63ea124e IEFRAME!Ordinal231+0xb3c83
      # |36 0a19c854 77548e71 MSHTML+0x8d45e
      # |1b 0000008c`53b2c650 00007ffa`4631cfba ntdll!KiUserCallbackDispatcherContinue
      # |22 00000040`0597b770 00007ffa`36ddc0e3 0x40`90140fc3
      # |Could not allocate memory for stack trace
      assert asStackOutput[0] in [
        " # ChildEBP RetAddr  ",
        " # Child-SP          RetAddr           Call Site",
        "Could not allocate memory for stack trace"
      ], "Unknown stack header: %s\r\n%s" % (repr(asStackOutput[0]), "\r\n".join(asStackOutput));
      oStack = cStack();
      uFrameInstructionPointer = uInstructionPointer;
      uFrameIndex = 0;
      for sLine in asStackOutput[1:]:
        if re.match(srIgnoredWarningsAndErrors, sLine):
          continue;
        if uFrameIndex == uStackFramesCount:
          break;
        oMatch = re.match(r"^\s*%s\s*$" % (
          r"([0-9a-f]+)" r"\s+"                   # (frame_number) whitespace
          r"(?:"                                  # either {
            r"[0-9a-f`]+" r"\s+"                  #   stack_address whitespace
            r"([0-9a-f`]+)" r"\s+"                #   (return_address) whitespace
          r"|"                                    # } or {
            r"\(Inline(?: Function)?\)" r"\s+"  #   "(Inline" [" Function"] ")" whitespace
            r"\-{8}(?:`\-{8})?" r"\s+"            #   "--------" [`--------] whitespace
          r")"                                    # }
          r"(.+?)"                                # Symbol or address
        r"(?: \[(.+) @ (\d+)\])?"                 # [ "[" (source_file_path) " @ " (line_number) "]" ]
        ), sLine, re.I);
        assert oMatch, "Unknown stack output: %s\r\n%s" % (repr(sLine), "\r\n".join(asStackOutput));
        (sFrameIndex, sReturnAddress, sCdbSymbolOrAddress, sSourceFilePath, sSourceFileLineNumber) = oMatch.groups();
        # We may have already parsed this before, but we had to restart because of symbol loading issues. In this
        # case, we can continue to the next.
        if int(sFrameIndex, 16) < uFrameIndex:
          continue;
        uReturnAddress = sReturnAddress and long(sReturnAddress.replace("`", ""), 16);
        (
          uAddress,
          sUnloadedModuleFileName, oModule, uModuleOffset,
          oFunction, iFunctionOffset
        ) = oProcess.ftxSplitSymbolOrAddress(sCdbSymbolOrAddress);
        if oModule and not oModule.bSymbolsAvailable and uTryCount < dxConfig["uMaxSymbolLoadingRetries"]:
          # We will retry this to see if any symbol problems have been resolved:
          break;
        if uReturnAddress:
          # Check if we cached this:
          if uReturnAddress in dCache_toCallModuleAndFunction_by_uReturnAddress:
            toCallModuleAndFunction = dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress];
            if toCallModuleAndFunction:
              oModule, oFunction = dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress];
              uAddress = None;
              sUnloadedModuleFileName = None;
              uModuleOffset = None;
              iFunctionOffset = None; # Not known.
          else:
            # The symbol may not be correct when using export symbols, or if we're in a small branch that is not marked
            # correctly in the pdb (cdb will report the closest symbol, which may be for another function!).
            # We do have a return address and there may be a CALL instruction right before the return address that we
            # can use to find the correct symbol for the function.
            asDisassemblyBeforeReturnAddressOutput = oCdbWrapper.fasSendCommandAndReadOutput(
              ".if($vvalid(0x%X, 1)) { .if (by(0x%X) == 0xe8) { .if($vvalid(0x%X, 4)) { u 0x%X L1; }; }; }; $$ Get call instruction for %s" % \
              (uReturnAddress - 5, uReturnAddress - 5, uReturnAddress - 4, uReturnAddress -5, sCdbSymbolOrAddress),
            );
            if len(asDisassemblyBeforeReturnAddressOutput) == 0:
              dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress] = None;
            else:
              if len(asDisassemblyBeforeReturnAddressOutput) == 1:
                sDissassemblyBeforeReturnAddress = asDisassemblyBeforeReturnAddressOutput[0];
              else:
                assert len(asDisassemblyBeforeReturnAddressOutput) == 2, \
                    "Expected 1 or 2 lines of disassembly output, got %d:\r\n%s" % \
                    (len(asDisassemblyBeforeReturnAddressOutput), "\r\n".join(asDisassemblyBeforeReturnAddressOutput));
                # first line should be cdb_module_id ["!" function_name] [ "+"/"-" "0x" offset_from_module_or_function] ":"
                assert re.match(r"^\s*\w+(?:!.+?)?(?:[\+\-]0x[0-9A-F]+)?:\s*$", asDisassemblyBeforeReturnAddressOutput[0], re.I), \
                    "Unexpected disassembly output line 1:\r\n%s" % "\r\n".join(asDisassemblyBeforeReturnAddressOutput);
                sDissassemblyBeforeReturnAddress = asDisassemblyBeforeReturnAddressOutput[1];
              oDirectCallMatch = re.match(
                r"^[0-9a-f`]+"                         # instruction_address
                r"\s+e8[0-9a-f`]{8}"                   # space "e8" call_offset
                r"\s+call"                             # space "call" 
                r"\s+(\w+)!(.+?)"                      # space (cdb_module_id) "!" (function_name) 
                r"\s+\([0-9a-f`]+\)"                   # space "(" address ")"
                r"\s*$",                               # [space]
                sDissassemblyBeforeReturnAddress, re.I,
              );
              if oDirectCallMatch:
                sCallModuleCdbId, sCallSymbol = oDirectCallMatch.groups();
                oCallModule = oProcess.foGetModuleForCdbId(sCallModuleCdbId);
                oCallFunction = oCallModule.foGetOrCreateFunctionForSymbol(sCallSymbol);
                if oCallModule != oModule or oCallFunction != oFunction:
                  uAddress = None;
                  sUnloadedModuleFileName = None;
                  oModule = oCallModule;
                  uModuleOffset = None;
                  oFunction = oCallFunction;
                  iFunctionOffset = None; # Not known.
                dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress] = (oCallModule, oCallFunction);
              else:
                dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress] = None;
        # Symbols for a module with export symbol are untrustworthy unless the offset is zero. If the offset is not
        # zero, do not use the symbol, but rather the offset from the start of the module.
        if oFunction and iFunctionOffset not in xrange(dxConfig["uMaxExportFunctionOffset"]):
          if not oModule.bSymbolsAvailable:
            if uFrameInstructionPointer:
              # Calculate the offset the easy way.
              uModuleOffset = uFrameInstructionPointer - oModule.uStartAddress;
            else:
              # Calculate the offset the harder way.
              uFrameSymbolAddress = oCdbWrapper.fuGetValue("%s%+d" % (oFunction.sName, iFunctionOffset), "Get address of symbol");
              uModuleOffset = uFrameSymbolAddress - oModule.uStartAddress;
            oFunction = None;
            iFunctionOffset = None;
        uSourceFileLineNumber = sSourceFileLineNumber and long(sSourceFileLineNumber);
        oStackFrame = oStack.foCreateAndAddStackFrame(
          uIndex = uFrameIndex,
          sCdbSymbolOrAddress = sCdbSymbolOrAddress, 
          uInstructionPointer = uFrameInstructionPointer,
          uReturnAddress = uReturnAddress,
          uAddress = uAddress, 
          sUnloadedModuleFileName = sUnloadedModuleFileName,
          oModule = oModule, uModuleOffset = uModuleOffset, 
          oFunction = oFunction, iFunctionOffset = iFunctionOffset,
          sSourceFilePath = sSourceFilePath, uSourceFileLineNumber = uSourceFileLineNumber,
        );
        if uReturnAddress:
          # Last frame's return address is next frame's instruction pointer.
          uFrameInstructionPointer = uReturnAddress;
        uFrameIndex += 1;
      else:
        # No symbol loading problems found: we are done.
        break;
    oStack.bPartialStack = uFrameIndex == uStackFramesCount;
    return oStack;
