import hashlib, math, re;
from dxConfig import dxConfig;

cRegExp = type(re.compile("a"));

class cStackFrame(object):
  def __init__(oStackFrame, 
      oStack,
      uNumber,
      sCdbSymbolOrAddress,
      uInstructionPointer, uReturnAddress,
      uAddress,
      sUnloadedModuleFileName,
      oModule, uModuleOffset, 
      oFunction, iFunctionOffset,
      sSourceFilePath, uSourceFileLineNumber,
  ):
    oStackFrame.oStack = oStack;
    oStackFrame.uNumber = uNumber;
    oStackFrame.sCdbSymbolOrAddress = sCdbSymbolOrAddress;
    oStackFrame.uInstructionPointer = uInstructionPointer;
    oStackFrame.uReturnAddress = uReturnAddress;
    oStackFrame.uAddress = uAddress;
    oStackFrame.sUnloadedModuleFileName = sUnloadedModuleFileName;
    oStackFrame.oModule = oModule;
    oStackFrame.uModuleOffset = uModuleOffset;
    oStackFrame.oFunction = oFunction;
    oStackFrame.iFunctionOffset = iFunctionOffset;
    oStackFrame.sSourceFilePath = sSourceFilePath;
    oStackFrame.uSourceFileLineNumber = uSourceFileLineNumber;
    oStackFrame.oPreviousFrame = uNumber > 0 and oStack.aoFrames[uNumber - 1] or None;
    # Stack frames at the top may not be relevant to the crash (eg. ntdll.dll!RaiseException). The bIsHidden flag is
    # set for such frames to "hide" them. Frames that do not have a return address are inline frames and also not
    # considered relevant.
    oStackFrame.bIsHidden = uReturnAddress is None;
    if oFunction:
      oStackFrame.sAddress = oFunction.sName;
      if iFunctionOffset is None:
        oStackFrame.sAddress += " + ? (the exact offset is not known)";
      elif iFunctionOffset:
        oStackFrame.sAddress += " %s 0x%X" % (iFunctionOffset > 0 and "+" or "-", abs(iFunctionOffset));
      oStackFrame.sSimplifiedAddress = oFunction.sSimplifiedName;
      oStackFrame.sUniqueAddress = oFunction.sUniqueName;
    elif oModule:
      oStackFrame.sAddress = "%s + 0x%X" % (oModule.sBinaryName, uModuleOffset);
      oStackFrame.sSimplifiedAddress = "%s+0x%X" % (oModule.sSimplifiedName, uModuleOffset);
      # Adding offset makes it more unique and thus allows distinction between two different crashes, but seriously
      # reduces the chance of getting the same id for the same crash in different builds.
      oStackFrame.sUniqueAddress = "%s+0x%X" % (oModule.sUniqueName, uModuleOffset);
    elif sUnloadedModuleFileName:
      oStackFrame.sAddress = "%s + 0x%X" % (sUnloadedModuleFileName, uModuleOffset);
      oStackFrame.sSimplifiedAddress = "%s+0x%X" % (sUnloadedModuleFileName, uModuleOffset);
      oStackFrame.sUniqueAddress = None;
    else:
      # It may be useful to check if the address is in executable memory (using !vprot). If it is not, the return
      # address is most likely incorrect and the validity of the entire stack is doubtful. This could have been caused
      # by stack corruption in the application or cdb failing to unwind the stack correctly. Both are interesting to
      # report. When I ever run into an example of this, I will implement it.
      oStackFrame.sAddress = "0x%X" % uAddress;
      oStackFrame.sSimplifiedAddress = None;
      oStackFrame.sUniqueAddress = None;
    if oStackFrame.sUniqueAddress is None:
      oStackFrame.sId = None;
    else:
      oHasher = hashlib.md5();
      oHasher.update(oStackFrame.sUniqueAddress);
      oStackFrame.sId = oHasher.hexdigest()[:dxConfig["uMaxStackFrameHashChars"]];

  def fbMatchesSymbol(oStackFrame, sSymbol):
    if sSymbol == None:
      # None means this frame should not have a symbol, if it does have a symbol, it does not match.
      return not oStackFrame.sSimplifiedAddress;
    # This frame should have a symbol, if it does not have a symbol, it does not match.
    if not oStackFrame.sSimplifiedAddress:
      return False;
    if isinstance(sSymbol, cRegExp):
      # Regular expression match:
      return sSymbol.match(oStackFrame.sSimplifiedAddress) is not None;
    assert isinstance(sSymbol, str), \
      "symbol must be a string or a regular expression object, got %s:%s" % (type(sSymbol).__name__, repr(sSymbol));
      
    if sSymbol == "*":
      # "*" means this frame can have any symbol in any module.
      return True;
    if sSymbol[:2] == "*!":
      # "*!xxx" means this frame should match the given function symbol in any module.
      tsSimplifiedAddress = oStackFrame.sSimplifiedAddress.split("!", 1);
      # Compare the function names:
      return len(tsSimplifiedAddress) == 2 and tsSimplifiedAddress[1].lower() == sSymbol[2:].lower();
    if sSymbol[-2:] == "!*":
      # "xxx!*" means this frame should match any function in the given module.
      tsSimplifiedAddress = oStackFrame.sSimplifiedAddress.split("!", 1);
      # Compare the function names:
      return len(tsSimplifiedAddress) == 2 and tsSimplifiedAddress[0].lower() == sSymbol[:-2].lower();
    # Match entire simplified address:
    return oStackFrame.sSimplifiedAddress.lower() == sSymbol.lower();
