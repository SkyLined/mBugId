import os, re;
from cModule import cModule;
from cProcess_fauGetBytes import cProcess_fauGetBytes;
from cProcess_fdsSymbol_by_uAddressForPartialSymbol import cProcess_fdsSymbol_by_uAddressForPartialSymbol;
from cProcess_fEnsurePageHeapIsEnabled import cProcess_fEnsurePageHeapIsEnabled;
from cProcess_foGetHeapManagerDataForAddress import cProcess_foGetHeapManagerDataForAddress;
from cProcess_fsGet_String import cProcess_fsGetASCIIString, cProcess_fsGetUnicodeString;
from cProcess_ftxSplitSymbolOrAddress import cProcess_ftxSplitSymbolOrAddress;
from cProcess_fuGetValue import cProcess_fuGetValue;
from cProcess_fuGetValueForRegister import cProcess_fuGetValueForRegister;
from mWindowsAPI import *;

class cProcess(object):
  def __init__(oProcess, oCdbWrapper, uId):
    oProcess.oCdbWrapper = oCdbWrapper;
    oProcess.uId = uId;
    oProcess.bNew = True; # Will be set to False by `fCdbStdInOutThread` once running.
    oProcess.bTerminated = False; # Will be set to True by `foSetCurrentProcessAfterApplicationRan` once terminated
    
    # Modules will be cached here. They are discarded whenever the application is resumed.
    oProcess.__doModules_by_sCdbId = {};
    
    # We'll try to determine if page heap is enabled for every process. However, this may not always work. So until
    # we've successfully found out, the following value will be None. Once we know, it is set to True or False.
    oProcess.bPageHeapEnabled = None;
    
    # Process Information is only determined when needed and cached.
    oProcess.__oProcessInformation = None; 
    
    # oProcess.uPageSize is only determined when needed and cached
    oProcess.__uPageSize = None;
    
    # oProcess.__uIntegrityLevel is only determined when needed and cached
    oProcess.__uIntegrityLevel = None;
    
    # oProcess.oMainModule is only determined when needed and cached
    oProcess.__oMainModule = None; # .oMainModule is JIT
    
    # oProcess.aoModules is only determined when needed; it creates an entry in __doModules_by_sCdbId for every loaded
    # module and returns all the values in the first dict. Since this dict is cached, this only needs to be done once
    # until the cache is invalidated.
    oProcess.__bAllModulesEnumerated = False;
  
  def __foGetProcessInformation(oProcess):
    if oProcess.__oProcessInformation is None:
      oProcess.__oProcessInformation = cProcessInformation.foGetForId(oProcess.uId);
      assert oProcess.__oProcessInformation.sBinaryPath is not None, \
          "You cannot get process information for a 64-bit process from 32-bit Python";
    return oProcess.__oProcessInformation;
  
  @property
  def sBinaryName(oProcess):
    return oProcess.__foGetProcessInformation().sBinaryName;
  
  @property
  def sSimplifiedBinaryName(oProcess):
    # Windows filesystems are case-insensitive and the casing of the binary name may change between versions.
    # Lowercasing the name prevents this from resulting in location ids that differ in casing while still returning
    # a name that can be used to access the file.
    return oProcess.sBinaryName.lower();
  
  @property
  def sBinaryBasePath(oProcess):
    return os.path.dirname(oProcess.__foGetProcessInformation().sBinaryPath);
  
  @property
  def sCommandLine(oProcess):
    return oProcess.__foGetProcessInformation().sCommandLine;
  
  @property
  def sISA(oProcess):
    return oProcess.__foGetProcessInformation().sISA;
  
  @property
  def uPointerSize(oProcess):
    return {"x64": 8, "x86": 4}[oProcess.sISA];
  
  @property
  def uPageSize(oProcess):
    if oProcess.__uPageSize is None:
      oProcess.__uPageSize = oProcess.fuGetValueForRegister("$pagesize", "Get page size for process");
    return oProcess.__uPageSize;
  
  @property
  def uIntegrityLevel(oProcess):
    if oProcess.__uIntegrityLevel is None:
      oProcess.__uIntegrityLevel = fuGetProcessIntegrityLevelForId(oProcess.uId);
    return oProcess.__uIntegrityLevel;
  
  @property
  def oMainModule(oProcess):
    if oProcess.__oMainModule is None:
      uMainModuleStartAddress = oProcess.__foGetProcessInformation().uBinaryStartAddress;
      oProcess.__oMainModule = oProcess.foGetOrCreateModuleForStartAddress(uMainModuleStartAddress);
    return oProcess.__oMainModule;
  
  def foGetOrCreateModuleForStartAddress(oProcess, uStartAddress):
    for oModule in oProcess.__doModules_by_sCdbId.values():
      if oModule.uStartAddress == uStartAddress:
        return oModule;
    return cModule.foCreateForStartAddress(oProcess, uStartAddress);
  
  def foGetOrCreateModuleForCdbId(oProcess, sCdbId):
    if sCdbId not in oProcess.__doModules_by_sCdbId:
      return cModule.foCreateForCdbId(oProcess, sCdbId);
    return oProcess.__doModules_by_sCdbId[sCdbId];
  
  def foGetOrCreateModule(oProcess, uStartAddress, uEndAddress, sCdbId, sSymbolStatus):
    if sCdbId not in oProcess.__doModules_by_sCdbId:
      oProcess.__doModules_by_sCdbId[sCdbId] = cModule(oProcess, uStartAddress, uEndAddress, sCdbId, sSymbolStatus);
    return oProcess.__doModules_by_sCdbId[sCdbId];
  
  @property
  def aoModules(oProcess):
    if not oProcess.__bAllModulesEnumerated:
      oProcess.__bAllModulesEnumerated = True;
      return cModule.faoGetOrCreateAll(oProcess);
    return oProcess.__doModules_by_sCdbId.values();
  
  def fClearCache(oProcess):
    # Assume that all modules can be unloaded, except the main module.
    oProcess.__doModules_by_sCdbId = {};
    oProcess.__oMainModule = None;
    oProcess.__bAllModulesEnumerated = False;
  
  def fSelectInCdb(oProcess):
    oProcess.oCdbWrapper.fSelectProcess(oProcess.uId);
  
  def __str__(oProcess):
    return 'Process(%s %s #%d)' % (oProcess.sBinaryName, oProcess.sISA, oProcess.uProcessId);
  
  def ftxSplitSymbolOrAddress(oProcess, sSymbolOrAddress):
    return cProcess_ftxSplitSymbolOrAddress(oProcess, sSymbolOrAddress);
  
  def fEnsurePageHeapIsEnabled(oProcess):
    return cProcess_fEnsurePageHeapIsEnabled(oProcess);
    
  def fasGetStack(oProcess, sCdbCommand):
    return cProcess_fasGetStack(oProcess, sCdbCommand);
  
  def fuAddBreakpointForAddress(oProcess, uAddress, fCallback, uThreadId = None, sCommand = None):
    return oProcess.oCdbWrapper.fuAddBreakpointForAddress(
      uAddress = uAddress,
      fCallback = fCallback,
      uProcessId = oProcess.uId,
      uThreadId = uThreadId,
      sCommand = sCommand,
    );
  
  def fasExecuteCdbCommand(oProcess, sCommand, sComment, **dxArguments):
    # Make sure all commands send to cdb are send in the context of this process.
    oProcess.fSelectInCdb();
    return oProcess.oCdbWrapper.fasExecuteCdbCommand(sCommand, sComment, **dxArguments);
  
  def fuGetValue(oProcess, sValue, sComment):
    return cProcess_fuGetValue(oProcess, sValue, sComment);
  def fuGetValueForRegister(oProcess, sRegister, sComment):
    return cProcess_fuGetValueForRegister(oProcess, sRegister, sComment);
  def fdsSymbol_by_uAddressForPartialSymbol(oProcess, sSymbol, sComment):
    return cProcess_fdsSymbol_by_uAddressForPartialSymbol(oProcess, sSymbol, sComment);
  def fsGetSymbolForAddress(oProcess, sAddress, sComment):
    return cCdbWrapper_fsGetSymbolForAddress(oProcess, sAddress, sComment);
  def fsGetASCIIString(oProcess, sAddress, sComment):
    return cProcess_fsGetASCIIString(oProcess, sAddress, sComment);
  def fsGetUnicodeString(oProcess, sAddress, sComment):
    return cProcess_fsGetUnicodeString(oProcess, sAddress, sComment);
  def fauGetBytes(oProcess, uAddress, uSize, sComment):
    return cProcess_fauGetBytes(oProcess, uAddress, uSize, sComment);
  def foGetHeapManagerDataForAddress(oProcess, uAddress, sType = None):
    return cProcess_foGetHeapManagerDataForAddress(oProcess, uAddress, sType);

