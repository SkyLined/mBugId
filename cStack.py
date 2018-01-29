import re;
from cModule import cModule;
from cStackFrame import cStackFrame;
from dxConfig import dxConfig;
from ftoCallModuleAndFunctionFromCallInstructionForReturnAddress import ftoCallModuleAndFunctionFromCallInstructionForReturnAddress;

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
    oModule, uModuleOffset, #TODO naming inconsistency with iOffsetFromStartOfFunction
    oFunction, iOffsetFromStartOfFunction,
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
      oFunction, iOffsetFromStartOfFunction,
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
    # Create the stack object
    oProcess.fSelectInCdb();
    uStackFramesCount = min(dxConfig["uMaxStackFramesCount"], uSize);
    asStack = oProcess.fasGetStack("dps 0x%X L0x%X" % (pAddress, uStackFramesCount + 1));
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
        oFunction, iOffsetFromStartOfFunction
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
        oFunction = oFunction, iOffsetFromStartOfFunction = iOffsetFromStartOfFunction,
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
    # Get information on all modules in the current process
    # First frame's instruction pointer is exactly that:
    uInstructionPointer = oProcess.fuGetValueForRegister("$ip", "Get instruction pointer");
    # Cache symbols that are called based on the return address after the call.
    dCache_toCallModuleAndFunction_by_uReturnAddress = {};
    for uTryCount in xrange(dxConfig["uMaxSymbolLoadingRetries"] + 1):
      asStackOutput = oProcess.fasExecuteCdbCommand(
        sCommand = "kn 0x%X;" % (uStackFramesCount + 1),
        sComment = "Get stack",
      );
      # Here are some lines you might expect to parse:
      # |00 (Inline) -------- chrome_child!WTF::RawPtr<blink::Document>::operator*+0x11
      # |03 0082ec08 603e2568 chrome_child!blink::XMLDocumentParser::startElementNs+0x105
      # |33 0082fb50 0030d4ba chrome!wWinMain+0xaa
      # |23 0a8cc578 66629c9b 0x66cf592a
      # |13 0a8c9cc8 63ea124e IEFRAME!Ordinal231+0xb3c83
      # |36 0a19c854 77548e71 MSHTML+0x8d45e
      # |1b 0000008c`53b2c650 00007ffa`4631cfba ntdll!KiUserCallbackDispatcherContinue
      # |22 00000040`0597b770 00007ffa`36ddc0e3 0x40`90140fc3
      # |---
      # |Could not allocate memory for stack trace
      uStackStartIndex = 0;
      while asStackOutput[uStackStartIndex] in [
        "Unable to read dynamic function table list head",
      ]:
        # Ignored warning/error
        uStackStartIndex += 1;
      assert asStackOutput[uStackStartIndex] in [
        " # ChildEBP RetAddr  ",
        " # Child-SP          RetAddr           Call Site",
        "Could not allocate memory for stack trace",
      ], "Unknown stack header: %s\r\n%s" % (repr(asStackOutput[uStackStartIndex]), "\r\n".join(asStackOutput));
      uStackStartIndex += 1;
      oStack = cStack();
      uFrameInstructionPointer = uInstructionPointer;
      uFrameIndex = 0;
      for sLine in asStackOutput[uStackStartIndex:]:
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
          oFunction, iOffsetFromStartOfFunction
        ) = oProcess.ftxSplitSymbolOrAddress(sCdbSymbolOrAddress);
        if oModule and not oModule.bSymbolsAvailable and uTryCount < dxConfig["uMaxSymbolLoadingRetries"]:
          # We will retry this to see if any symbol problems have been resolved:
          break;
        if uReturnAddress:
          # See if we can get better symbol information from the call instruction.
          # First check cache.
          if uReturnAddress in dCache_toCallModuleAndFunction_by_uReturnAddress:
            toCallModuleAndFunction = dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress];
          else:
            toCallModuleAndFunction = ftoCallModuleAndFunctionFromCallInstructionForReturnAddress(oProcess, uReturnAddress);
            # Cache this info.
            dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress] = toCallModuleAndFunction;
          if toCallModuleAndFunction and (oModule, oFunction) != toCallModuleAndFunction:
            # The call instruction for this return address is assumed to give us better information; use that:
            (oModule, oFunction) = dCache_toCallModuleAndFunction_by_uReturnAddress[uReturnAddress];
            uAddress = None;
            sUnloadedModuleFileName = None;
            uModuleOffset = None;
            iOffsetFromStartOfFunction = None;
        # Symbols for a module with export symbol are untrustworthy unless the offset is zero. If the offset is not
        # zero, do not use the symbol, but rather the offset from the start of the module.
        if oFunction and (iOffsetFromStartOfFunction not in xrange(dxConfig["uMaxExportFunctionOffset"])):
          if not oModule.bSymbolsAvailable:
            if uFrameInstructionPointer:
              # Calculate the offset the easy way.
              uModuleOffset = uFrameInstructionPointer - oModule.uStartAddress;
            else:
              # Calculate the offset the harder way.
              uFunctionAddress = oProcess.fuGetAddressForSymbol(oFunction.sName);
              uModuleOffset = uFunctionAddress + iOffsetFromStartOfFunction - oModule.uStartAddress;
            oFunction = None;
            iOffsetFromStartOfFunction = None;
        uSourceFileLineNumber = sSourceFileLineNumber and long(sSourceFileLineNumber);
        oStackFrame = oStack.foCreateAndAddStackFrame(
          uIndex = uFrameIndex,
          sCdbSymbolOrAddress = sCdbSymbolOrAddress, 
          uInstructionPointer = uFrameInstructionPointer,
          uReturnAddress = uReturnAddress,
          uAddress = uAddress, 
          sUnloadedModuleFileName = sUnloadedModuleFileName,
          oModule = oModule, uModuleOffset = uModuleOffset, 
          oFunction = oFunction, iOffsetFromStartOfFunction = iOffsetFromStartOfFunction,
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
