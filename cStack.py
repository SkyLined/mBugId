import re;

from mNotProvided import fAssertType;

# local imports are at the end of this file to avoid import loops.

gbDebugOutput = False;

grbIgnoredWarningsAndErrors = re.compile(
  rb"^(?:"
    # These warnings and errors are ignored:
    rb"Unable to read dynamic function table list head"
  rb")$"
);
grb_dps_StackOutputLine = re.compile(
  rb"\A\s*"                                 # optional whitespace
  rb"[0-9A-F`]+"                            #   stack_address
  rb"\s+"                                   # whitespace
  rb"([0-9A-F`]+)"                          #   **return_address**
  rb"\s+"                                   # whitespace
  rb"(.+?)"                                 # **symbol_or_address**
  rb"(?:"                                   # optional {
    rb"\s+"                                 #   whitespace
    rb"\["                                  #   "["
    rb"(.+)"                                #   **source_file_path**
    rb" @ "                                 #   " @ "
    rb"(\d+)"                               #   **line_number**
    rb"\]"                                  #   "]"
  rb")?"                                    # }
  rb"\s*\Z"                                 # optional whitespace
);
grb_kn_StackOutputHeaderLine = re.compile(
  rb"\A\s*"                                 # optional whitespace
  rb"#"                                     # "#"
  rb"\s+"                                   # whitespace
  rb"Child(?:EBP|\-SP)"                     # "ChildEBP" or "Child-SP"
  rb"\s+"                                   # whitespace
  rb"RetAddr"                               # "RetAddr"
  rb"(?:"                                    # optional {
    rb"\s+"                                 #   whitespace
    rb"Call Site"                           #   "Call Site"
  rb")?"                                    # }
  rb"\s*\Z"                                 # optional whitespace
);
grb_kn_StackOutputLine = re.compile(
  rb"\A\s*"                                 # optional whitespace
  rb"[0-9a-f]+"                             # frame_number
  rb"\s+"                                   # whitespace
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
  rb"\s*\Z"                                 # optional whitespace
);

# Windows loads kernel32 and ntdll and they do some thread initialization. These
# functions are hidden on the stack because they are unlikely to be relevant:
rbOSThreadInitializationSymbols = re.compile(
  rb"\A("
    rb"kernel32\.dll!BaseThreadInitThunk"
  rb"|"
    rb"kernel32\.dll!BaseThreadInitXfgThunk" # New in Windows 11
  rb"|"
    rb"ntdll\.dll!_*RtlUserThreadStart"
  rb")\Z"
);
# Windows Common RunTime does some thread initialization too. These functions
# are implemented in the main binary for the process, so we check that first
# and then match their function names. If found they are hidden on the stack
# because they are unlikely to be relevant:
rbCRTThreadInitializationFunctionSymbols = re.compile(
  rb"\A("
    rb"__scrt_common_main_seh"
  rb"|"
    rb"invoke_main"
  rb")\Z"
);
# Windows compile time mitigations add even more complexity:
rbMitigationFunctionSymbols = re.compile(
  rb"\A("
    rb"ntdll\.dll!LdrpDispatchUserCallTarget"
  rb")\Z"
);

class cStack(object):
  def __init__(oSelf):
    oSelf.aoFrames = [];
    oSelf.bPartialStack = True;
    oSelf.__du0CallTargetAddress_by_uReturnAddress = {};
  
  def foCreateAndAddStackFrame(oSelf,
    oProcess,
    sbCdbSymbolOrAddress,
    u0InstructionPointer, u0ReturnAddress,
    u0Address,
    sb0UnloadedModuleFileName,
    o0Module, u0ModuleOffset, #TODO naming inconsistency with iOffsetFromStartOfFunction
    o0Function, i0OffsetFromStartOfFunction,
    sb0SourceFilePath = None, u0SourceFileLineNumber = None,
  ):
    oStackFrame = cStackFrame(
      oSelf,
      uIndex = len(oSelf.aoFrames),
      sbCdbSymbolOrAddress = sbCdbSymbolOrAddress,
      u0InstructionPointer = u0InstructionPointer, u0ReturnAddress = u0ReturnAddress,
      u0Address = u0Address,
      sb0UnloadedModuleFileName = sb0UnloadedModuleFileName,
      o0Module = o0Module, u0ModuleOffset = u0ModuleOffset, 
      o0Function = o0Function, i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction,
      sb0SourceFilePath = sb0SourceFilePath, u0SourceFileLineNumber = u0SourceFileLineNumber,
    );
    # Hide stack frames that make no sense because they are not in executable memory.
    if oStackFrame.s0IsHiddenBecause is None and oStackFrame.u0Address:
      o0FrameCodeVirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(oStackFrame.u0Address);
      if not o0FrameCodeVirtualAllocation or not o0FrameCodeVirtualAllocation.bExecutable:
        # This frame's instruction pointer does not point to executable memory; it is probably invalid.
        oStackFrame.s0IsHiddenBecause = "Address 0x%X is not in executable memory" % oStackFrame.u0Address;
    # Hide stack frames that are part of the thread initialization code.
    if oStackFrame.o0Function and oStackFrame.o0Function.oModule.sb0SimplifiedName:
      if rbOSThreadInitializationSymbols.match(oStackFrame.o0Function.sbSimplifiedName):
        oStackFrame.s0IsHiddenBecause = "Part of OS thread initialization code";
      elif rbMitigationFunctionSymbols.match(oStackFrame.o0Function.sbSimplifiedName):
        oStackFrame.s0IsHiddenBecause = "Part of OS vulnerability mitigation code";
      elif oStackFrame.o0Function.oModule == oProcess.oMainModule and rbCRTThreadInitializationFunctionSymbols.match(oStackFrame.o0Function.sbSymbol):
        oStackFrame.s0IsHiddenBecause = "Part of CRT thread initialization code";
    oSelf.aoFrames.append(oStackFrame);
    return oStackFrame;
  
  def fbHideTopFramesIfTheyMatchSymbols(oSelf, r0bSymbols, sReason, bAlsoHideNoneFrames = False):
    if bAlsoHideNoneFrames:
      # If we are hiding None frame, r0bSymbols can be None
      fAssertType("r0bSymbols", r0bSymbols, re.Pattern, None);
    else:
      # If we are not hiding None frame, r0bSymbols can not be None, or it would never be hiding anything!
      fAssertType("r0bSymbols", r0bSymbols, re.Pattern);
    fAssertType("sReason", sReason, str);
    fAssertType("bAlsoHideNoneFrames", bAlsoHideNoneFrames, bool);
    uFrameIndex = 0;
    while uFrameIndex < len(oSelf.aoFrames) and (oSelf.aoFrames[uFrameIndex].s0IsHiddenBecause is not None):
      uFrameIndex += 1;
    if uFrameIndex == len(oSelf.aoFrames):
      return False; # All frames are hidden!?
    uStartFrameIndex = uFrameIndex;
    # Match as many frames as possible.
    while uFrameIndex < len(oSelf.aoFrames) and oSelf.aoFrames[uFrameIndex].fbHideIfItMatchesSymbols(r0bSymbols, sReason, bAlsoHideNoneFrames):
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
    u0InstructionPointer = None; # Unknown for first frame.
    oStack.bPartialStack = False;
    for sbLine in asbStack:
      if len(oStack.aoFrames) >= uStackFramesCount:
        oStack.bPartialStack = True;
        break;
      ob_dps_StackOutputLineMatch = grb_dps_StackOutputLine.match(sbLine, re.I);
      assert ob_dps_StackOutputLineMatch, \
            "Unknown stack output: %s\r\n%s" % \
            (repr(sbLine), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbStack));
      sbReturnAddress, sbCdbSymbolOrAddress, sb0SourceFilePath, sb0SourceFileLineNumber = \
          ob_dps_StackOutputLineMatch.groups();
      (
        u0Address,
        sb0UnloadedModuleFileName, o0Module, u0ModuleOffset,
        o0Function, i0OffsetFromStartOfFunction
      ) = oProcess.ftxSplitSymbolOrAddress(sbCdbSymbolOrAddress);
      u0ReturnAddress = fu0ValueFromCdbHexOutput(sbReturnAddress);
      oStack.foCreateAndAddStackFrame(
        oProcess,
        sbCdbSymbolOrAddress = sbCdbSymbolOrAddress, 
        u0InstructionPointer = u0InstructionPointer,
        u0ReturnAddress = u0ReturnAddress,
        u0Address = u0Address, 
        sb0UnloadedModuleFileName = sb0UnloadedModuleFileName,
        o0Module = o0Module, u0ModuleOffset = u0ModuleOffset, 
        o0Function = o0Function, i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction,
        sb0SourceFilePath = sb0SourceFilePath, u0SourceFileLineNumber = int(sb0SourceFileLineNumber) if sb0SourceFileLineNumber else None,
      );
      # Last frame's return address is next frame's instruction pointer.
      u0InstructionPointer = u0ReturnAddress;
    return oStack;
  
  @classmethod
  def foCreate(cStack, oProcess, oThread, uStackFramesCount):
    # Get information on all modules in the current process
    # First frame's instruction pointer is exactly that:
    o0StackVirtualAllocation = oThread.o0StackVirtualAllocation;
    u0InstructionPointer = oThread.fu0GetRegister(b"*ip");
    if gbDebugOutput: print("Analyzing stack...");
    asbStackOutput = oProcess.fasbGetStack(
      b"kn 0x%X;" % (uStackFramesCount + 1),
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
    # Ignored warning/error
    while asbStackOutput[uStackStartIndex]  == b"Unable to read dynamic function table list head":
      uStackStartIndex += 1;
    # Make sure we have a header for a stack output or a known error:
    assert (
      grb_kn_StackOutputHeaderLine.match(asbStackOutput[uStackStartIndex])
      or asbStackOutput[uStackStartIndex] == b"Could not allocate memory for stack trace"
    ), \
        "Unknown stack header: %s\r\n%s" % (
          repr(asbStackOutput[uStackStartIndex]),
          "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbStackOutput)
        );
    # Skip the stack output header or error and process remaining lines (0 in case of error).
    uStackStartIndex += 1;
    oStack = cStack();
    u0FrameInstructionPointer = u0InstructionPointer;
    oStack.bPartialStack = False;
    for sbLine in asbStackOutput[uStackStartIndex:]:
      if len(oStack.aoFrames) == uStackFramesCount:
        if gbDebugOutput: print("- Stop processing stack because we have enough frames.");
        oStack.bPartialStack = True;
        break;
      
      if gbDebugOutput: print("* Stack line: %s" % repr(sbLine));
      
      if grbIgnoredWarningsAndErrors.match(sbLine):
        if gbDebugOutput: print("  -> Ignored warning/error");
        continue;
      
      ob_kn_StackOutputLineMatch = grb_kn_StackOutputLine.match(sbLine);
      assert ob_kn_StackOutputLineMatch, \
          "Unknown stack output: %s\r\n%s" % \
          (repr(sbLine), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbStackOutput));
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
      # to create a new frame that has the combined correct information from both.
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
        if gbDebugOutput: print(" -> Ignore bogus frame: %s" % oIncorrectFrame);
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
      oStackFrame = oStack.foCreateAndAddStackFrame(
        oProcess,
        sbCdbSymbolOrAddress = sbCdbSymbolOrAddress,
        u0InstructionPointer = u0FrameInstructionPointer,
        u0ReturnAddress = u0ReturnAddress,
        u0Address = u0Address,
        sb0UnloadedModuleFileName = sb0UnloadedModuleFileName,
        o0Module = o0Module, u0ModuleOffset = u0ModuleOffset,
        o0Function = o0Function, i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction,
        sb0SourceFilePath = sb0SourceFilePath, u0SourceFileLineNumber = u0SourceFileLineNumber,
      );
      if gbDebugOutput: print("  -STACK-> %s" % oStackFrame);
      if u0ReturnAddress is not None:
        if u0ReturnAddress not in oStack.__du0CallTargetAddress_by_uReturnAddress:
          oStack.__du0CallTargetAddress_by_uReturnAddress[u0ReturnAddress] = \
              oProcess.fu0GetTargetAddressForCallInstructionReturnAddress(u0ReturnAddress);
        u0CallTargetAddressFromInstruction = oStack.__du0CallTargetAddress_by_uReturnAddress[u0ReturnAddress];
        if u0CallTargetAddressFromInstruction is None:
          if gbDebugOutput: print("  -> Return address 0x%X => no CALL instruction found." % u0ReturnAddress);
        else:
          sb0CallTargetSymbol = oProcess.fsb0GetSymbolForAddress(u0CallTargetAddressFromInstruction, b"Get function symbol for CALL instruction target address 0x%X" % u0CallTargetAddressFromInstruction);
          if sb0CallTargetSymbol is None:
            # We cannot use the CALL we found before the return address to determine the correct symbol.
            if gbDebugOutput: print("  -> Return address 0x%X => CALL 0x%X (no symbol)" % (u0ReturnAddress, u0CallTargetAddressFromInstruction));
          else:
            if gbDebugOutput: print("  -> Return address 0x%X => CALL %s (0x%X)" % (u0ReturnAddress, fsCP437FromBytesString(sb0CallTargetSymbol), u0CallTargetAddressFromInstruction));
            # In certain situations, it might make sense to overwrite the stack given by cdb...
            (
              u0CallTargetAddress, # Should be None since we have a symbol (== module and function)
              sb0CallTargetUnloadedModuleFileName, o0CallTargetModule, u0CallTargetModuleOffsetForCallTarget,
              o0CallTargetFunction, i0CallTargetOffsetFromStartOfFunction
            ) = oProcess.ftxSplitSymbolOrAddress(sb0CallTargetSymbol);
            # We only add this as a frame if we have found a proper function symbol:
            if o0CallTargetFunction and (not o0Function or o0CallTargetFunction.sbUniqueName != o0Function.sbUniqueName):
              # I have not looked into how to get this info:
              sb0CallTargetSourceFilePath = None;
              u0CallTargetSourceFileLineNumber = None;
              # The offsets we get above are for the call target, but we want to have the offset for the frame instruction pointer, sOSISA
              # so we will have to do some math:
              if u0FrameInstructionPointer is None:
                i0CallTargetOffsetFromStartOfFunction = None;
              else:
                i0CallTargetOffsetFromStartOfFunction = None if o0CallTargetFunction is None else u0FrameInstructionPointer - u0CallTargetAddressFromInstruction;
              oStackFrame = oStack.foCreateAndAddStackFrame(
                oProcess,
                sbCdbSymbolOrAddress = sb0CallTargetSymbol,
                u0InstructionPointer = u0FrameInstructionPointer,
                u0ReturnAddress = u0ReturnAddress,
                u0Address = u0CallTargetAddress,
                sb0UnloadedModuleFileName = sb0CallTargetUnloadedModuleFileName,
                o0Module = o0CallTargetModule, u0ModuleOffset = u0CallTargetModuleOffsetForCallTarget,
                o0Function = o0CallTargetFunction, i0OffsetFromStartOfFunction = i0CallTargetOffsetFromStartOfFunction,
                sb0SourceFilePath = sb0CallTargetSourceFilePath, u0SourceFileLineNumber = u0CallTargetSourceFileLineNumber,
              );
              if gbDebugOutput: print("  -CALL-> %s" % oStackFrame);
      # Let's see what this stack frame's return address is. We can cache this info to speed this process up.
      if u0ReturnAddress:
        # Last frame's return address is next frame's instruction pointer.
        u0FrameInstructionPointer = u0ReturnAddress;
    return oStack;

from .cStackFrame import cStackFrame;
from .dxConfig import dxConfig;
from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from .mCP437 import fsCP437FromBytesString;
