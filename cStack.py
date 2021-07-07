import re;

from mNotProvided import *;

gbDebugOutput = False;

grbIgnoredWarningsAndErrors = re.compile(
  rb"^(?:"
    # These warnings and errors are ignored:
    rb"Unable to read dynamic function table list head"
  rb")$"
);
grb_dps_StackOutputLine = re.compile(
  rb"^\s*"                                  # optional whitespace
  rb"[0-9A-F`]+"                            #   stack_address
  rb"\s+"                                   # whilespace
  rb"([0-9A-F`]+)"                          #   **return_address**
  rb"\s+"                                   # whilespace
  rb"(.+?)"                                 # **symbol_or_address**
  rb"(?:"                                   # optional {
    rb"\s+"                                 #   whitespace
    rb"\["                                  #   "["
    rb"(.+)"                                #   **source_file_path**
    rb" @ "                                 #   " @ "
    rb"(\d+)"                               #   **line_number**
    rb"\]"                                  #   "]"
  rb")?"                                    # }
  rb"\s*$"                                  # optional whitespace
);
grb_kn_StackOutputLine = re.compile(
  rb"^\s*"                                  # optional whitespace
  rb"[0-9a-f]+"                             # frame_number
  rb"\s+"                                   # whilespace
  rb"(?:"                                   # either {
    rb"[0-9a-f`]+"                          #   **stack_address**
    rb"\s+"                                 #   whitespace
    rb"([0-9a-f`]+)"                        #   **return_address**
  rb"|"                                     # } or {
    rb"\(Inline(?: Function)?\)"            #   "(Inline" optional{ " Function" } ")"
    rb"\s+"                                 #   whitespace
    rb"\-{8}(?:`\-{8})?"                    #   "--------" optional{ "`--------" }
  rb")"                                     # }
  rb"\s+"                                   #   whitespace
  rb"(.+?)"                                 # **symbol_or_address**
  rb"(?:"                                   # optional {
    rb"\s+"                                 #   whitespace
    rb"\["                                  #   "["
    rb"(.+)"                                #   **source_file_path**
    rb" @ "                                 #   " @ "
    rb"(\d+)"                               #   **line_number**
    rb"\]"                                  #   "]"
  rb")?"                                    # }
  rb"\s*$"                                  # optional whitespace
);

# Windows loads kernel32 and ntdll and they do some thread initialization. These
# functions are hidden on the stack because they are unlikely to be relevant:
rbOSThreadInitialisationSymbols = re.compile(
  rb"\A("
    rb"kernel32\.dll!BaseThreadInitThunk"
  rb"|"
    rb"ntdll\.dll!_*RtlUserThreadStart"
  rb")\Z"
);
# Windows Common RunTime does some thread initialization too. These functions
# are implemented in the main binary for the process, so we check that first
# and then match their function names. If found they are hidden on the stack
# because they are unlikely to be relevant:
rbCRTThreadInitialisationFunctionSymbols = re.compile(
  rb"\A("
    rb"__scrt_common_main_seh"
  rb"|"
    rb"invoke_main"
  rb")\Z"
);

class cStack(object):
  def __init__(oSelf):
    oSelf.aoFrames = [];
    oSelf.bPartialStack = True;
    oSelf.__dCache_t0oCallModuleAndFunction_by_uReturnAddress = {};
  
  def fbCreateAndAddStackFrame(oSelf,
    oProcess,
    uIndex,
    sbCdbSymbolOrAddress,
    u0InstructionPointer, u0ReturnAddress,
    u0Address,
    sb0UnloadedModuleFileName,
    o0Module, u0ModuleOffset, #TODO naming inconsistency with iOffsetFromStartOfFunction
    o0Function, i0OffsetFromStartOfFunction,
    sb0SourceFilePath = None, u0SourceFileLineNumber = None,
  ):
    # frames must be created in order:
    assert uIndex == len(oSelf.aoFrames), \
        "Unexpected frame index %d vs %d" % (uIndex, len(oSelf.aoFrames));
    uMaxStackFramesCount = dxConfig["uMaxStackFramesCount"];
    
    oStackFrame = cStackFrame(
      oSelf,
      uIndex = uIndex,
      sbCdbSymbolOrAddress = sbCdbSymbolOrAddress,
      u0InstructionPointer = u0InstructionPointer, u0ReturnAddress = u0ReturnAddress,
      u0Address = u0Address,
      sb0UnloadedModuleFileName = sb0UnloadedModuleFileName,
      o0Module = o0Module, u0ModuleOffset = u0ModuleOffset, 
      o0Function = o0Function, i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction,
      sb0SourceFilePath = sb0SourceFilePath, u0SourceFileLineNumber = u0SourceFileLineNumber,
    );
    if oStackFrame.sb0UniqueAddress is None and oStackFrame.u0ReturnAddress:
      # This frame has no symbol but it has a return address and the caller frame exists.
      u0FindoutSymbolFromReturnAddress = oStackFrame.u0ReturnAddress;
      uReturnAddressFrameIndex = uIndex;
      s0DoNotUpdateFrameIfAddressIs = None;
    elif oStackFrame.u0ReturnAddress is None and len(oSelf.aoFrames) > 0:
      # This frame is reported as an inline function, but that may not be true. If a function
      # was called from this frame, the return address of the previously added frame could
      # help determine the real function name for this frame.
      u0FindoutSymbolFromReturnAddress = oSelf.aoFrames[-1].u0ReturnAddress;
      uReturnAddressFrameIndex = uIndex - 1;
      s0DoNotUpdateFrameIfAddressIs = oSelf.aoFrames[-1].sb0UniqueAddress;
    else:
      u0FindoutSymbolFromReturnAddress = None;
    if u0FindoutSymbolFromReturnAddress is not None:
      # We have an inlined function on the stack, that may actually not be an inlined function:
      if oStackFrame.u0ReturnAddress in oSelf.__dCache_t0oCallModuleAndFunction_by_uReturnAddress:
        t0oCallModuleAndFunction = oSelf.__dCache_t0oCallModuleAndFunction_by_uReturnAddress[u0FindoutSymbolFromReturnAddress];
      else:
        t0oCallModuleAndFunction = oSelf.__dCache_t0oCallModuleAndFunction_by_uReturnAddress[u0FindoutSymbolFromReturnAddress] = \
            ft0oCallModuleAndFunctionFromCallInstructionForReturnAddress(oProcess, u0FindoutSymbolFromReturnAddress);
      if t0oCallModuleAndFunction and (oStackFrame.o0Module, oStackFrame.o0Function) != t0oCallModuleAndFunction:
        # The call instruction found at this frame's return address is assumed to give us better information:
        (oModule, oFunction) = t0oCallModuleAndFunction;
        if oStackFrame.u0Address:
          uFunctionAddress = oProcess.fuGetAddressForSymbol(oFunction.sbCdbId);
          i0OffsetFromStartOfFunction = oStackFrame.u0Address - uFunctionAddress;
          if -0x1000 < i0OffsetFromStartOfFunction < 0x1000:
            if gbDebugOutput: print("Stackframe @ 0x%X, function @ 0x%X, offset too large (%d)" % (oStackFrame.u0Address, uFunctionAddress, i0OffsetFromStartOfFunction));
            i0OffsetFromStartOfFunction = None;
          else:
            if gbDebugOutput: print("Stackframe @ 0x%X, function @ 0x%X, offset = %d" % (oStackFrame.u0Address, uFunctionAddress, i0OffsetFromStartOfFunction));
        else:
          i0OffsetFromStartOfFunction = None;
        oUpdatedStackFrame = cStackFrame(
          oSelf,
          uIndex = uIndex,
          sbCdbSymbolOrAddress = sbCdbSymbolOrAddress,
          u0InstructionPointer = u0InstructionPointer, u0ReturnAddress = u0ReturnAddress,
          u0Address = None,
          sb0UnloadedModuleFileName = None,
          o0Module = oModule, u0ModuleOffset = None, 
          o0Function = oFunction, i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction,
          sb0SourceFilePath = sb0SourceFilePath, u0SourceFileLineNumber = u0SourceFileLineNumber,
        );
        if s0DoNotUpdateFrameIfAddressIs is None or s0DoNotUpdateFrameIfAddressIs != oUpdatedStackFrame.sb0UniqueAddress:
          if gbDebugOutput: print("- Used return address 0x%X for frame #%d to update frame %sfrom %s to %s" % (
            u0FindoutSymbolFromReturnAddress,
            uReturnAddressFrameIndex,
            ("#%d " % uIndex) if uIndex != uReturnAddressFrameIndex else "",
            repr(oStackFrame), repr(oUpdatedStackFrame),
          ));
          oStackFrame = oUpdatedStackFrame;
        else:
          if gbDebugOutput: print("* Did not use return address 0x%X for frame #%d to update frame %sfrom %s to %s: matches %s" % (
            u0FindoutSymbolFromReturnAddress,
            uReturnAddressFrameIndex,
            ("#%d " % uIndex) if uIndex != uReturnAddressFrameIndex else "",
            repr(oStackFrame), repr(oUpdatedStackFrame),
            s0DoNotUpdateFrameIfAddressIs,
          ));
    # Hide stack frames that make no sense because they are not in executable memory.
    if oStackFrame.s0IsHiddenBecause is None and oStackFrame.u0Address:
      oFrameCodeVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(oStackFrame.u0Address);
      if not oFrameCodeVirtualAllocation.bExecutable:
        # This frame's instruction pointer does not point to executable memory; it is probably invalid.
        oStackFrame.s0IsHiddenBecause = "Address 0x%X is not in executable memory" % oStackFrame.u0Address;
    # Hide stack frames that are part of the thread initialization code.
    if oStackFrame.o0Function and oStackFrame.o0Function.oModule.sb0SimplifiedName:
      if rbOSThreadInitialisationSymbols.match(oStackFrame.o0Function.sbSimplifiedName):
        if gbDebugOutput: print("- %s because it is part of thread initialization code" % repr(oStackFrame));
        oStackFrame.s0IsHiddenBecause = "Part of OS thread initialization code";
      elif oStackFrame.o0Function.oModule.sbCdbId == oProcess.oMainModule.sbCdbId and rbCRTThreadInitialisationFunctionSymbols.match(oStackFrame.o0Function.sbSymbol):
        if gbDebugOutput: print("- %s because it is part of thread initialization code" % repr(oStackFrame));
        oStackFrame.s0IsHiddenBecause = "Part of CRT thread initialization code";
    oSelf.aoFrames.append(oStackFrame);
    return True;
  
  def fbHideTopFramesIfTheyMatchSymbols(oSelf, rbSymbols, sReason):
    fAssertType("rbSymbols", rbSymbols, re.Pattern);
    uFrameIndex = 0;
    while uFrameIndex < len(oSelf.aoFrames) and (oSelf.aoFrames[uFrameIndex].s0IsHiddenBecause is not None):
      uFrameIndex += 1;
    if uFrameIndex == len(oSelf.aoFrames):
      return False; # All frames are hidden!?
    uStartFrameIndex = uFrameIndex;
    # Match as many frames as possible.
    while oSelf.aoFrames[uFrameIndex].fbHideIfItMatchesSymbols(rbSymbols, sReason):
      uFrameIndex += 1;
    return uStartFrameIndex != uFrameIndex; # Return true if any frames matched
  
  @classmethod
  def foCreateFromAddress(cStack, oProcess, pAddress, uSize):
    # Create the stack object
    oProcess.fSelectInCdb();
    uStackFramesCount = min(dxConfig["uMaxStackFramesCount"], uSize);
    asbStack = oProcess.fasbGetStack(b"dps 0x%X L0x%X" % (pAddress, uStackFramesCount + 1));
    if not asbStack: return None;
    oStack = cStack(asbStack);
    # Here are some lines you might expect to parse:
    # |TODO put something here...
    uFrameIndex = 0;
    u0InstructionPointer = None; # Unknown for first frame.
    for sbLine in asbStack:
      if uFrameIndex == uStackFramesCount:
        break;
      ob_dps_StackOutputLineMatch = grb_dps_StackOutputLine.match(sbLine, re.I);
      assert ob_dps_StackOutputLineMatch, \
            "Unknown stack output: %s\r\n%s" % (repr(sbLine), b"\r\n".join(asbStackOutput));
      sbReturnAddress, sbCdbSymbolOrAddress, sb0SourceFilePath, sb0SourceFileLineNumber = \
          ob_dps_StackOutputLineMatch.groups();
      (
        u0Address,
        sb0UnloadedModuleFileName, o0Module, u0ModuleOffset,
        o0Function, i0OffsetFromStartOfFunction
      ) = oProcess.ftxSplitSymbolOrAddress(sbCdbSymbolOrAddress);
      u0ReturnAddress = fu0ValueFromCdbHexOutput(sbReturnAddress);
      if not oStack.fbCreateAndAddStackFrame(
        oProcess,
        uIndex = uFrameIndex,
        sbCdbSymbolOrAddress = sbCdbSymbolOrAddress, 
        u0InstructionPointer = u0InstructionPointer,
        u0ReturnAddress = u0ReturnAddress,
        u0Address = u0Address, 
        sb0UnloadedModuleFileName = sb0UnloadedModuleFileName,
        o0Module = o0Module, u0ModuleOffset = u0ModuleOffset, 
        o0Function = o0Function, i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction,
        sb0SourceFilePath = sb0SourceFilePath, u0SourceFileLineNumber = int(sb0SourceFileLineNumber) if sb0SourceFileLineNumber else None,
      ):
        break; # Stack frame is part of ntdll loader; nothing else of interest is expected to be on the stack.
      # Last frame's return address is next frame's instruction pointer.
      u0InstructionPointer = u0ReturnAddress;
      uFrameIndex += 1;
    oStack.bPartialStack = uFrameIndex == uStackFramesCount;
    return oStack;
  
  @classmethod
  def foCreate(cStack, oProcess, oThread, uStackFramesCount):
    # Get information on all modules in the current process
    # First frame's instruction pointer is exactly that:
    o0StackVirtualAllocation = oThread.o0StackVirtualAllocation;
    u0InstructionPointer = oThread.fu0GetRegister(b"*ip");
    for uTryCount in range(dxConfig["uMaxSymbolLoadingRetries"] + 1):
      asbStackOutput = oProcess.fasbExecuteCdbCommand(
        sbCommand = b"kn 0x%X;" % (uStackFramesCount + 1),
        sb0Comment = b"Get stack",
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
      while asbStackOutput[uStackStartIndex] in [
        b"Unable to read dynamic function table list head",
      ]:
        # Ignored warning/error
        uStackStartIndex += 1;
      assert asbStackOutput[uStackStartIndex] in [
        b" # ChildEBP RetAddr  ",
        b" # Child-SP          RetAddr           Call Site",
        b"Could not allocate memory for stack trace",
      ], "Unknown stack header: %s\r\n%s" % (repr(asbStackOutput[uStackStartIndex]), b"\r\n".join(asbStackOutput));
      uStackStartIndex += 1;
      oStack = cStack();
      u0FrameInstructionPointer = u0InstructionPointer;
      uFrameIndex = 0;
      for sbLine in asbStackOutput[uStackStartIndex:]:
        if gbDebugOutput: print("Stack line: %s" % repr(sbLine));
        if grbIgnoredWarningsAndErrors.match(sbLine):
          if gbDebugOutput: print("- Ignored");
          continue;
        if uFrameIndex == uStackFramesCount:
          if gbDebugOutput: print("- Enough frames");
          break;
        ob_kn_StackOutputLineMatch = grb_kn_StackOutputLine.match(sbLine);
        assert ob_kn_StackOutputLineMatch, \
            "Unknown stack output: %s\r\n%s" % (repr(sbLine), b"\r\n".join(asbStackOutput));
        (sb0ReturnAddress, sbCdbSymbolOrAddress, sb0SourceFilePath, sb0SourceFileLineNumber) = \
            ob_kn_StackOutputLineMatch.groups();
        u0ReturnAddress = fu0ValueFromCdbHexOutput(sb0ReturnAddress);
        (
          u0Address,
          sb0UnloadedModuleFileName, o0Module, u0ModuleOffset,
          o0Function, i0OffsetFromStartOfFunction
        ) = oProcess.ftxSplitSymbolOrAddress(sbCdbSymbolOrAddress);
        u0SourceFileLineNumber = int(sb0SourceFileLineNumber) if sb0SourceFileLineNumber else None;
        # There are bugs in cdb's stack unwinding; it can produce an incorrect frame followed by a bogus frames. The
        # incorrect frame will have a return address that points to the stack (obviously incorrect) and the bogus
        # frame will have a function address that is the same as this return address. The bogus frame will have the
        # correct return address for the incorrect frame.
        # We will try to detect the bogus frame, then copy relevant information from the incorrect frame and delete it
        # to create a new frame that hase the combined correct information from both.
        if (
          u0Address # This frame's function does not point to a symbol, but an address (potentially the stack)
          and oStack.aoFrames # This is not the first frame.
          and (
            o0StackVirtualAllocation is None # If possible check if this frame's function 
            or o0StackVirtualAllocation.fbContainsAddress(u0Address) # points to the stack
          )
          and oStack.aoFrames[-1].u0ReturnAddress == u0Address # The previous frame return address == this frame's function.
        ):
          # Remove the incorrect frame, and undo the update to the frame index.
          oIncorrectFrame = oStack.aoFrames.pop();
          if gbDebugOutput: print("- remove bogus frame: %s" % oIncorrectFrame);
          uFrameIndex -= 1;
          # Use most of the values from the incorrect frame, except the return address for the combined frame:
          sbCdbSymbolOrAddress = oIncorrectFrame.sbCdbSymbolOrAddress;
          u0FrameInstructionPointer = oIncorrectFrame.u0InstructionPointer;
          # u0ReturnAddress = oIncorrectFrame.u0ReturnAddress; # this is the only thing valid in the bogus frame.
          u0Address = oIncorrectFrame.u0Address;
          sb0UnloadedModuleFileName = oIncorrectFrame.sb0UnloadedModuleFileName;
          o0Module = oIncorrectFrame.o0Module;
          u0ModuleOffset = oIncorrectFrame.u0ModuleOffset;
          o0Function = oIncorrectFrame.o0Function;
          i0OffsetFromStartOfFunction = oIncorrectFrame.i0OffsetFromStartOfFunction;
          sb0SourceFilePath = oIncorrectFrame.sb0SourceFilePath;
          u0SourceFileLineNumber = oIncorrectFrame.u0SourceFileLineNumber;
        elif o0Module and not o0Module.bSymbolsAvailable and uTryCount < dxConfig["uMaxSymbolLoadingRetries"]:
          if gbDebugOutput: print("- Symbol issues; will retry");
          # We will retry this to see if any symbol problems have been resolved:
          break;
        # Symbols for a module with export symbol are untrustworthy unless the offset is zero. If the offset is not
        # zero, do not use the symbol, but rather the offset from the start of the module.
        if o0Function and (i0OffsetFromStartOfFunction not in range(dxConfig["uMaxExportFunctionOffset"])):
          assert o0Module, \
              "Function but no module!?";
          if not o0Module.bSymbolsAvailable:
            if u0FrameInstructionPointer:
              # Calculate the offset the easy way.
              u0ModuleOffset = u0FrameInstructionPointer - o0Module.uStartAddress;
            else:
              # Calculate the offset the harder way.
              uFunctionAddress = oProcess.fuGetAddressForSymbol(o0Function.sbCdbId);
              u0ModuleOffset = uFunctionAddress + (i0OffsetFromStartOfFunction or 0) - o0Module.uStartAddress;
            o0Function = None;
            i0OffsetFromStartOfFunction = None;
        if not oStack.fbCreateAndAddStackFrame(
          oProcess,
          uIndex = uFrameIndex,
          sbCdbSymbolOrAddress = sbCdbSymbolOrAddress,
          u0InstructionPointer = u0FrameInstructionPointer,
          u0ReturnAddress = u0ReturnAddress,
          u0Address = u0Address,
          sb0UnloadedModuleFileName = sb0UnloadedModuleFileName,
          o0Module = o0Module, u0ModuleOffset = u0ModuleOffset,
          o0Function = o0Function, i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction,
          sb0SourceFilePath = sb0SourceFilePath, u0SourceFileLineNumber = u0SourceFileLineNumber,
        ):
          break; # Stack frame is part of ntdll loader; nothing else of interest is expected to be on the stack.
        uFrameIndex += 1;
        if u0ReturnAddress:
          # Last frame's return address is next frame's instruction pointer.
          u0FrameInstructionPointer = u0ReturnAddress;
      else:
        # No symbol loading problems found: we are done.
        break;
    oStack.bPartialStack = uFrameIndex == uStackFramesCount;
    return oStack;

from .cModule import cModule;
from .cStackFrame import cStackFrame;
from .dxConfig import dxConfig;
from .ft0oCallModuleAndFunctionFromCallInstructionForReturnAddress import ft0oCallModuleAndFunctionFromCallInstructionForReturnAddress;
from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
