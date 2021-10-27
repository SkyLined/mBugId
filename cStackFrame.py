import hashlib, math, re;

from mNotProvided import *;

class cStackFrame(object):
  def __init__(oSelf, 
    oStack,
    uIndex,
    sbCdbSymbolOrAddress,
    u0InstructionPointer, u0ReturnAddress,
    u0Address,
    sb0UnloadedModuleFileName,
    o0Module, u0ModuleOffset, 
    o0Function, i0OffsetFromStartOfFunction,
    sb0SourceFilePath, u0SourceFileLineNumber,
  ):
    fAssertType("oStack", oStack, cStack);
    fAssertType("uIndex", uIndex, int, None);
    fAssertType("sbCdbSymbolOrAddress", sbCdbSymbolOrAddress, bytes);
    fAssertType("u0InstructionPointer", u0InstructionPointer, int, None);
    fAssertType("u0ReturnAddress", u0ReturnAddress, int, None);
    fAssertType("u0Address", u0Address, int, None);
    fAssertType("sb0UnloadedModuleFileName", sb0UnloadedModuleFileName, bytes, None);
    fAssertType("o0Module", o0Module, cModule, None);
    fAssertType("u0ModuleOffset", u0ModuleOffset, int, None);
    fAssertType("o0Function", o0Function, cFunction, None);
    fAssertType("i0OffsetFromStartOfFunction", i0OffsetFromStartOfFunction, int, None);
    fAssertType("sb0SourceFilePath", sb0SourceFilePath, bytes, None);
    fAssertType("u0SourceFileLineNumber", u0SourceFileLineNumber, int, None);
    oSelf.oStack = oStack;
    oSelf.uIndex = uIndex;
    oSelf.sbCdbSymbolOrAddress = sbCdbSymbolOrAddress;
    oSelf.u0InstructionPointer = u0InstructionPointer;
    oSelf.u0ReturnAddress = u0ReturnAddress;
    oSelf.u0Address = u0Address;
    oSelf.sb0UnloadedModuleFileName = sb0UnloadedModuleFileName;
    oSelf.o0Module = o0Module;
    oSelf.u0ModuleOffset = u0ModuleOffset;
    oSelf.o0Function = o0Function;
    oSelf.i0OffsetFromStartOfFunction = i0OffsetFromStartOfFunction;
    oSelf.sb0SourceFilePath = sb0SourceFilePath;
    oSelf.u0SourceFileLineNumber = u0SourceFileLineNumber;
    # Frames that do not have a return address are inline frames.
    oSelf.bIsInline = u0ReturnAddress is None;
    # Stack frames at the top may not be relevant to the crash (eg. ntdll.dll!RaiseException). These can be hidden
    # by giving a reason for doing so.
    oSelf.s0IsHiddenBecause = None;
    # Stack frames that are part of the BugId will be marked as such:
    oSelf.bIsPartOfId = False;
    oSelf.fUpdateProperties();
  
  def fUpdateProperties(oSelf):
    if oSelf.o0Function:
      sbOffsetFromStartOfFunction = (
        (b" + ???") if oSelf.i0OffsetFromStartOfFunction is None else
        (b" %s 0x%X" % (
          oSelf.i0OffsetFromStartOfFunction > 0 and b"+" or b"-",
          abs(oSelf.i0OffsetFromStartOfFunction))
        ) if oSelf.i0OffsetFromStartOfFunction != 0 else
        b""
      );
      oSelf.sbAddress = oSelf.o0Function.sbName + sbOffsetFromStartOfFunction;
      oSelf.sb0SimplifiedAddress = oSelf.o0Function.sbSimplifiedName;
      oSelf.sb0UniqueAddress = oSelf.o0Function.sbUniqueName;
    elif oSelf.o0Module:
      sbModuleOffset = (b"0x%X" % oSelf.u0ModuleOffset) if oSelf.u0ModuleOffset is not None else b"???";
      oSelf.sbAddress = b"%s + %s" % (oSelf.o0Module.sb0BinaryName or b"<unknown module>", sbModuleOffset);
      oSelf.sb0SimplifiedAddress = oSelf.o0Module.sb0SimplifiedName and (b"%s+%s" % (oSelf.o0Module.sb0SimplifiedName, sbModuleOffset));
      # Adding offset makes it more unique and thus allows distinction between two different crashes, but seriously
      # reduces the chance of getting the same id for the same crash in different builds.
      oSelf.sb0UniqueAddress = oSelf.o0Module.sb0UniqueName and (b"%s+%s" % (oSelf.o0Module.sb0UniqueName, sbModuleOffset));
    elif oSelf.sb0UnloadedModuleFileName:
      sbModuleOffset = (b"0x%X" % oSelf.u0ModuleOffset) if oSelf.u0ModuleOffset is not None else b"???";
      oSelf.sbAddress = b"%s + %s" % (oSelf.sb0UnloadedModuleFileName, sbModuleOffset);
      oSelf.sb0SimplifiedAddress = b"%s+%s" % (oSelf.sbUnloadedModuleFileName, sbModuleOffset);
      oSelf.sb0UniqueAddress = None;
    else:
      assert oSelf.u0Address is not None, \
          "No address!?";
      # It may be useful to check if the address is in executable memory (using !vprot). If it is not, the return
      # address is most likely incorrect and the validity of the entire stack is doubtful. This could have been caused
      # by stack corruption in the application or cdb failing to unwind the stack correctly. Both are interesting to
      # report. When I ever run into an example of this, I will implement it.
      oSelf.sbAddress = b"0x%X" % oSelf.u0Address;
      oSelf.sb0SimplifiedAddress = None;
      oSelf.sb0UniqueAddress = None;
    if oSelf.sb0UniqueAddress is None:
      oSelf.sId = "???";
    else:
      oHasher = hashlib.md5();
      oHasher.update(oSelf.sb0UniqueAddress);
      oSelf.sId = oHasher.hexdigest()[:dxConfig["uMaxStackFrameHashChars"]];
  
  @property
  def bHidden(oSelf):
    return oSelf.s0IsHiddenBecause is not None;
  
  def fbHideIfItMatchesSymbols(oSelf, r0bSymbols, sReason, bAlsoHideNoneFrames):
    if bAlsoHideNoneFrames:
      # If we are hiding None frame, r0bSymbols can be None
      fAssertType("r0bSymbols", r0bSymbols, re.Pattern, None);
    else:
      # If we are not hiding None frame, r0bSymbols can not be None, or it would never be hiding anything!
      fAssertType("r0bSymbols", r0bSymbols, re.Pattern);
    fAssertType("sReason", sReason, str);
    fAssertType("bAlsoHideNoneFrames", bAlsoHideNoneFrames, bool);
    # If this frame does not have a symbol, hide it if bAlsoHideNoneFrames is True.
    # If this frame has a symbol, hide it if matches the regular expression (if any).
    if (
      bAlsoHideNoneFrames if oSelf.sb0SimplifiedAddress is None else
      (r0bSymbols and r0bSymbols.match(oSelf.sb0SimplifiedAddress))
    ):
      oSelf.s0IsHiddenBecause = sReason;
      return True;
    return False;
  
  def __str__(oSelf):
    return "#%d %s (hash=%s%s)" % (oSelf.uIndex, str(oSelf.sbAddress, "ascii", "strict"), oSelf.sId, ", hidden: %s" % oSelf.s0IsHiddenBecause if oSelf.bHidden else "");
  def __repr__(oSelf):
    return "<cStackFrame %s>" % oSelf;

from .cStack import cStack;
from .cModule import cModule;
from .cFunction import cFunction;
from .dxConfig import dxConfig;
