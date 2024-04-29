import os;

from mWindowsAPI import fsHexNumber;

from ..cFunction import cFunction;

class cModule(object):
  def __init__(oSelf, oProcess, oWindowsAPIModule):
    oSelf.oProcess = oProcess;
    oSelf.oWindowsAPIModule = oWindowsAPIModule;
    oSelf.__sb0CdbId = None;
    oSelf.__doFunction_by_sbSymbol = {};
    oSelf.sISA = oProcess.sISA; # x86/x64 processes are assumed to only load x86/x64 modules respectively.
  
  def __repr__(oSelf):
    return "<cBugId.cModule (process 0x%X, %s, cdb id=%s, binary=%s)>(#%X)" % (
      oSelf.oProcess.uId,
      oSelf.oWindowsAPIModule,
      oSelf.sbCdbId,
      (oSelf.oWindowsAPIModule.s0BinaryPath or "<unknown>"),
      id(oSelf),
    );
  
  def foGetOrCreateFunctionForSymbol(oSelf, sbSymbol):
    if sbSymbol not in oSelf.__doFunction_by_sbSymbol:
      oSelf.__doFunction_by_sbSymbol[sbSymbol] = cFunction(oSelf, sbSymbol);
    return oSelf.__doFunction_by_sbSymbol[sbSymbol];
  
  @property
  def uStartAddress(oSelf):
    return oSelf.oWindowsAPIModule.uStartAddress;
  
  @property
  def s0BinaryPath(oSelf):
    return oSelf.oWindowsAPIModule.s0BinaryPath;
  
  @property
  def s0BinaryName(oSelf):
    s0BinaryPath = oSelf.s0BinaryPath;
    return os.path.basename(s0BinaryPath) if s0BinaryPath is not None else None;
  @property
  def sb0BinaryName(oSelf):
    s0BinaryName = oSelf.s0BinaryName;
    return bytes(s0BinaryName, "ascii", "replace") if s0BinaryName is not None else None;
  
  @property
  def sb0SimplifiedName(oSelf):
    sb0BinaryName = oSelf.sb0BinaryName;
    return sb0BinaryName.lower() if sb0BinaryName else None;
  
  @property
  def sb0UniqueName(oSelf):
    sb0BinaryName = oSelf.sb0BinaryName;
    return sb0BinaryName.lower() if sb0BinaryName else None;
  
  def fbIsCdbIdCached(oSelf):
    return oSelf.__sb0CdbId is not None;
  @property
  def sbCdbId(oSelf):
    if oSelf.__sb0CdbId is None:
      sb0FirstSymbolInModule = oSelf.oProcess.fsb0GetSymbolForAddress(
        oSelf.uStartAddress,
        b"Start address of module %s" % (oSelf.sb0BinaryName or b"<unknown>")
      );
      assert sb0FirstSymbolInModule, \
          "Cannot get any symbol for %s" % oSelf;
      # This could be "<cdbid>" or "<cdbid>!<symbol name>", split it and
      # get only the cdbid.
      asbModuleAndSymbol = sb0FirstSymbolInModule.split(b"!", 1);
      oSelf.__sb0CdbId = asbModuleAndSymbol[0];
    return oSelf.__sb0CdbId;
  @sbCdbId.setter
  def sbCdbId(oSelf, sbCdbId):
    oSelf.__sb0CdbId = sbCdbId;

  def fLoadSymbols(oSelf):
    if oSelf.oProcess.oCdbWrapper.bDoNotLoadSymbols:
      return;
    if oSelf.s0BinaryPath and oSelf.oProcess.oCdbWrapper.fbHaveSymbolsBeenLoadedForBinaryPath(oSelf.s0BinaryPath):
      return; # No need to do this again.
    if oSelf.sb0BinaryName:
      oSelf.oProcess.fasbExecuteCdbCommand(
        b"ld /f \"%s\"" % oSelf.sb0BinaryName,
        b"Load symbols for module @ 0x%X" % (oSelf.uStartAddress,),
      );
    else:
      oSelf.oProcess.fasbExecuteCdbCommand(
        b"ld %s" % oSelf.sbCdbId,
        b"Load symbols for module @ 0x%X" % (oSelf.uStartAddress,),
      );
    # Track for which binaries symbols have been loaded.
    if oSelf.s0BinaryPath:
      oSelf.oProcess.oCdbWrapper.fMarkSymbolsAsLoadedForBinaryPath(oSelf.s0BinaryPath);

  def __str__(oSelf):
    return "Module %s (%s) at %s" % (
      repr(oSelf.__sb0CdbId)[1:] if oSelf.__sb0CdbId is not None else "<cdb id not cached>",
      oSelf.s0BinaryPath,
      fsHexNumber(oSelf.uStartAddress),
    );