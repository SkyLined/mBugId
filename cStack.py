import re;
from cStackFrame import cStackFrame;
from dxConfig import dxConfig;

class cStack(object):
  def __init__(oStack, asCdbLines):
    oStack.asCdbLines = asCdbLines;
    oStack.aoFrames = [];
    oStack.bPartialStack = True;
    oStack.uHashFramesCount = dxConfig["uStackHashFramesCount"];
  
  def fCreateAndAddStackFrame(oStack,
    uNumber,
    sCdbSymbolOrAddress,
    uInstructionPointer, uReturnAddress,
    uAddress,
    sUnloadedModuleFileName,
    oModule, uModuleOffset,
    oFunction, iFunctionOffset,
    sSourceFilePath = None, uSourceFileLineNumber = None,
  ):
    # frames must be created in order:
    assert uNumber == len(oStack.aoFrames), \
        "Unexpected frame number %d vs %d" % (uNumber, len(oStack.aoFrames));
    uMaxStackFramesCount = dxConfig["uMaxStackFramesCount"];
    oStackFrame = cStackFrame(
      oStack,
      uNumber,
      sCdbSymbolOrAddress,
      uInstructionPointer, uReturnAddress,
      uAddress,
      sUnloadedModuleFileName,
      oModule, uModuleOffset, 
      oFunction, iFunctionOffset,
      sSourceFilePath, uSourceFileLineNumber,
    );
    oStack.aoFrames.append(oStackFrame);
    
  @classmethod
  def foCreateFromAddress(cStack, oCdbWrapper, pAddress, uSize):
    # Get information on all modules in the current process
    doModules_by_sCdbId = oCdbWrapper.fdoGetModulesByCdbIdForCurrentProcess();
    if not oCdbWrapper.bCdbRunning: return None;
    # Create the stack object
    uStackFramesCount = min(dxConfig["uMaxStackFramesCount"], uSize);
    asStack = oCdbWrapper.fasGetStack("dps 0x%X L0x%X" % (pAddress, uStackFramesCount + 1));
    if not asStack: return None;
    oStack = cStack(asStack);
    # Here are some lines you might expect to parse:
    # |TODO put something here...
    uFrameNumber = 0;
    uInstructionPointer = None; # Unknown for first frame.
    for sLine in asStack:
      if uFrameNumber == uStackFramesCount:
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
      ) = oCdbWrapper.ftxSplitSymbolOrAddress(sCdbSymbolOrAddress, doModules_by_sCdbId);
      uSourceFileLineNumber = sSourceFileLineNumber and long(sSourceFileLineNumber);
      uReturnAddress = sReturnAddress and long(sReturnAddress.replace("`", ""), 16);
      oStack.fCreateAndAddStackFrame(
        uNumber = uFrameNumber,
        sCdbSymbolOrAddress = sCdbSymbolOrAddress, 
        uInstructionPointer = uInstructionPointer,
        uReturnAddress = uReturnAddress,
        uAddress = uAddress, 
        sUnloadedModuleFileName = sUnloadedModuleFileName,
        oModule = oModule, uModuleOffset = uModuleOffset, 
        oFunction = oFunction, iFunctionOffset = iFunctionOffset,
        sSourceFilePath = sSourceFilePath, uSourceFileLineNumber = uSourceFileLineNumber,
      );
      if uReturnAddress: # Last frame's return address is next frame's instruction pointer.
        uInstructionPointer = uReturnAddress;
      uFrameNumber += 1;
    oStack.bPartialStack = uFrameNumber == uStackFramesCount;
    return oStack;
  
  @classmethod
  def foCreate(cStack, oCdbWrapper, uStackFramesCount):
    # Get information on all modules in the current process
    doModules_by_sCdbId = oCdbWrapper.fdoGetModulesByCdbIdForCurrentProcess();
    if not oCdbWrapper.bCdbRunning: return None;
    # First frame's instruction pointer is exactly that:
    uInstructionPointer = oCdbWrapper.fuGetValue("@$ip");
    # Create the stack object
    asStack = oCdbWrapper.fasGetStack("kn 0x%X" % (uStackFramesCount + 1));
    if not asStack: return None;
    oStack = cStack(asStack);
    sHeader = asStack.pop(0);
    assert re.sub(r"\s+", " ", sHeader.strip()) in ["# ChildEBP RetAddr", "# Child-SP RetAddr Call Site", "Could not allocate memory for stack trace"], \
        "Unknown stack header: %s" % repr(sHeader);
    # Here are some lines you might expect to parse:
    # |00 (Inline) -------- chrome_child!WTF::RawPtr<blink::Document>::operator*+0x11
    # |03 0082ec08 603e2568 chrome_child!blink::XMLDocumentParser::startElementNs+0x105
    # |33 0082fb50 0030d4ba chrome!wWinMain+0xaa
    # |23 0a8cc578 66629c9b 0x66cf592a
    # |13 0a8c9cc8 63ea124e IEFRAME!Ordinal231+0xb3c83
    # |36 0a19c854 77548e71 MSHTML+0x8d45e
    # |1b 0000008c`53b2c650 00007ffa`4631cfba ntdll!KiUserCallbackDispatcherContinue
    # |22 00000040`0597b770 00007ffa`36ddc0e3 0x40`90140fc3
    # |WARNING: Frame IP not in any known module. Following frames may be wrong.
    # |WARNING: Stack unwind information not available. Following frames may be wrong.
    # |Could not allocate memory for stack trace
    uFrameNumber = 0;
    for sLine in asStack:
      if not re.match(r"^(?:%s)$" % "|".join([
        # These warnings and errors are ignored:
        r"WARNING: Frame IP not in any known module\. Following frames may be wrong\.",
        r"WARNING: Stack unwind information not available\. Following frames may be wrong\.",
        r"\*\*\* ERROR: Module load completed but symbols could not be loaded for .*",
        r"\*\*\* WARNING: Unable to verify checksum for .*",
        r"Unable to read dynamic function table list head",
      ]), sLine):
        if uFrameNumber == uStackFramesCount:
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
        assert oMatch, "Unknown stack output: %s\r\n%s" % (repr(sLine), "\r\n".join(asStack));
        (sFrameNumber, sReturnAddress, sCdbSymbolOrAddress, sSourceFilePath, sSourceFileLineNumber) = oMatch.groups();
        assert uFrameNumber == int(sFrameNumber, 16), "Unexpected frame number: %s vs %d" % (sFrameNumber, uFrameNumber);
        uReturnAddress = sReturnAddress and long(sReturnAddress.replace("`", ""), 16);
        (
          uAddress,
          sUnloadedModuleFileName, oModule, uModuleOffset,
          oFunction, iFunctionOffset
        ) = oCdbWrapper.ftxSplitSymbolOrAddress(sCdbSymbolOrAddress, doModules_by_sCdbId);
        if uReturnAddress:
          # The symbol is not know or the offset is negative or very large: this may not be the correct symbol.
          # We do have a return address and there may be a CALL instruction right before the return address that we
          # can use to find the correct symbol for the function.
          asDisassemblyBeforeReturnAddressOutput = oCdbWrapper.fasSendCommandAndReadOutput(
            ".if (by(0x%X) == 0xe8) { .if($vvalid(0x%X, 4)) { u 0x%X L1; }; }; $$ Get call instruction for %s" % \
            (uReturnAddress - 5, uReturnAddress - 4, uReturnAddress -5, sCdbSymbolOrAddress),
          );
          if not oCdbWrapper.bCdbRunning: return None;
          if len(asDisassemblyBeforeReturnAddressOutput) == 0:
#            print "--- %s => invalid" % sCdbSymbolOrAddress;
            pass;
          else:
            if len(asDisassemblyBeforeReturnAddressOutput) == 1:
              sDissassemblyBeforeReturnAddress = asDisassemblyBeforeReturnAddressOutput[0];
            else:
              assert len(asDisassemblyBeforeReturnAddressOutput) == 2, \
                  "Expected 1 or 2 lines of disassembly output, got %d:\r\n%s" % \
                  (len(asDisassemblyBeforeReturnAddressOutput), "\r\n".join(asDisassemblyBeforeReturnAddressOutput));
              # first line should be cdb_module_id "!" function_name [ "+"/"-" "0x" offset_from_function] ":"
              assert re.match(r"^\s*\w+!.+?(?:[\+\-]0x[0-9A-F]+)?:\s*$", asDisassemblyBeforeReturnAddressOutput[0], re.I), \
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
              oCallModule = doModules_by_sCdbId[sCallModuleCdbId];
              oCallFunction = oCallModule.foGetOrCreateFunction(sCallSymbol);
              if oCallModule != oModule or oCallFunction != oFunction:
#                print "@@@ %s => %s!%s" % (sCdbSymbolOrAddress, sCallModuleCdbId, sCallSymbol);
                uAddress = None;
                sUnloadedModuleFileName = None;
                oModule = oCallModule;
                uModuleOffset = None;
                oFunction = oCallFunction;
                iFunctionOffset = None; # Not known.
#              else:
#                print "=== %s => %s!%s" % (sCdbSymbolOrAddress, sCallModuleCdbId, sCallSymbol);
#            else:
#              print "??? %s => %s" % (sCdbSymbolOrAddress, sDissassemblyBeforeReturnAddress);
        uSourceFileLineNumber = sSourceFileLineNumber and long(sSourceFileLineNumber);
        oStack.fCreateAndAddStackFrame(
          uNumber = uFrameNumber,
          sCdbSymbolOrAddress = sCdbSymbolOrAddress, 
          uInstructionPointer = uInstructionPointer,
          uReturnAddress = uReturnAddress,
          uAddress = uAddress, 
          sUnloadedModuleFileName = sUnloadedModuleFileName,
          oModule = oModule, uModuleOffset = uModuleOffset, 
          oFunction = oFunction, iFunctionOffset = iFunctionOffset,
          sSourceFilePath = sSourceFilePath, uSourceFileLineNumber = uSourceFileLineNumber,
        );
        if uReturnAddress: # Last frame's return address is next frame's instruction pointer.
          uInstructionPointer = uReturnAddress;
        uFrameNumber += 1;
    oStack.bPartialStack = uFrameNumber == uStackFramesCount;
    return oStack;
