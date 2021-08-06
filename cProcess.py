import os, re;
from .cModule import cModule;
from .cProcess_fEnsurePageHeapIsEnabled import cProcess_fEnsurePageHeapIsEnabled;
from .cProcess_fo0GetHeapManagerDataForAddress import cProcess_fo0GetHeapManagerDataForAddress;
from .cProcess_ftxSplitSymbolOrAddress import cProcess_ftxSplitSymbolOrAddress;
from .cProcess_fuGetAddressForSymbol import cProcess_fuGetAddressForSymbol;
from mWindowsAPI import cProcess as cWindowsAPIProcess, oSystemInfo;

class cProcess(object):
  def __init__(oProcess, oCdbWrapper, uId):
    oProcess.oCdbWrapper = oCdbWrapper;
    oProcess.uId = uId;
    oProcess.bTerminated = False; # Will be set to True by `cCdbWrapper_fHandleCurrentApplicationProcessTermination` once terminated
    
    # Modules will be cached here. They are discarded whenever the application is resumed.
    oProcess.__doModules_by_sbCdbId = {};
    
    # We'll try to determine if page heap is enabled for every process. However, this may not always work. So until
    # we've successfully found out, the following value will be None. Once we know, it is set to True or False.
    oProcess.bPageHeapEnabled = None;
    
    # Process Information is only determined when needed and cached.
    oProcess.__oWindowsAPIProcess = None; 
    
    # oProcess.__uIntegrityLevel is only determined when needed and cached
    oProcess.__uIntegrityLevel = None;
    
    # oProcess.oMainModule is only determined when needed and cached
    oProcess.__oMainModule = None; # .oMainModule is JIT
    
    # oProcess.aoModules is only determined when needed; it creates an entry in __doModules_by_sbCdbId for every loaded
    # module and returns all the values in the first dict. Since this dict is cached, this only needs to be done once
    # until the cache is invalidated.
    oProcess.__bAllModulesEnumerated = False;
  
  @property
  def oWindowsAPIProcess(oProcess):
    if oProcess.__oWindowsAPIProcess is None:
      oProcess.__oWindowsAPIProcess = cWindowsAPIProcess(oProcess.uId);
    return oProcess.__oWindowsAPIProcess;
  
  def foGetWindowsAPIThreadForId(oProcess, uThreadId):
    return oProcess.oWindowsAPIProcess.foGetThreadForId(uThreadId);
  
  @property
  def sSimplifiedBinaryName(oProcess):
    # Windows filesystems are case-insensitive and the casing of the binary name may change between versions.
    # Lowercasing the name prevents this from resulting in location ids that differ in casing while still returning
    # a name that can be used to access the file.
    return oProcess.sBinaryName.lower();
  
  @property
  def oMainModule(oProcess):
    if oProcess.__oMainModule is None:
      uMainModuleStartAddress = oProcess.oWindowsAPIProcess.uBinaryStartAddress;
      oProcess.__oMainModule = oProcess.fo0GetOrCreateModuleForStartAddress(uMainModuleStartAddress);
      assert oProcess.__oMainModule, \
          "Cannot find main module for binary start address 0x%X!?" % uMainModuleStartAddress;
    return oProcess.__oMainModule;
  
  def fo0GetOrCreateModuleForStartAddress(oProcess, uStartAddress):
    for oModule in oProcess.__doModules_by_sbCdbId.values():
      if oModule.uStartAddress == uStartAddress:
        return oModule;
    return cModule.fo0CreateForStartAddress(oProcess, uStartAddress);
  
  def fo0GetOrCreateModuleForCdbId(oProcess, sbCdbId):
    if sbCdbId not in oProcess.__doModules_by_sbCdbId:
      return cModule.fo0CreateForCdbId(oProcess, sbCdbId);
    return oProcess.__doModules_by_sbCdbId[sbCdbId];
  
  def foGetOrCreateModule(oProcess, uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus):
    if sbCdbId not in oProcess.__doModules_by_sbCdbId:
      oProcess.__doModules_by_sbCdbId[sbCdbId] = cModule(oProcess, uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus);
    return oProcess.__doModules_by_sbCdbId[sbCdbId];
  
  @property
  def aoModules(oProcess):
    if not oProcess.__bAllModulesEnumerated:
      oProcess.__bAllModulesEnumerated = True;
      return cModule.faoGetOrCreateAll(oProcess);
    return list(oProcess.__doModules_by_sbCdbId.values());
  
  def fClearCache(oProcess):
    # Assume that all modules can be unloaded, except the main module.
    oProcess.__doModules_by_sbCdbId = {};
    oProcess.__oMainModule = None;
    oProcess.__bAllModulesEnumerated = False;
  
  def fSelectInCdb(oProcess):
    oProcess.oCdbWrapper.fSelectProcessId(oProcess.uId);
  
  def __str__(oProcess):
    return 'Process(%s %s #%d)' % (oProcess.sBinaryName, oProcess.sISA, oProcess.uProcessId);
  
  def fasbGetStack(oProcess, sbCdbCommand):
    return cProcess_fasbGetStack(oProcess, sbCdbCommand);
  
  def fuAddBreakpointForAddress(oProcess, uAddress, fCallback, u0ThreadId = None, sb0Command = None):
    return oProcess.oCdbWrapper.fuAddBreakpointForProcessIdAndAddress(
      uProcessId = oProcess.uId,
      uAddress = uAddress,
      fCallback = fCallback,
      u0ThreadId = u0ThreadId,
      sb0Command = sb0Command,
    );
  
  def fasbExecuteCdbCommand(oProcess, sbCommand, sb0Comment, **dxArguments):
    # Make sure all commands send to cdb are send in the context of this process.
    oProcess.fSelectInCdb();
    return oProcess.oCdbWrapper.fasbExecuteCdbCommand(sbCommand, sb0Comment, **dxArguments);
  
  def fuGetValueForRegister(oProcess, sbRegister, sb0Comment):
    oProcess.fSelectInCdb();
    return oProcess.oCdbWrapper.fuGetValueForRegister(sbRegister, sb0Comment);
  
  # Proxy properties and methods to oWindowsAPIProcess
  @property
  def sISA(oProcess):
    return oProcess.oWindowsAPIProcess.sISA;
  @property
  def uPointerSize(oProcess):
    return oProcess.oWindowsAPIProcess.uPointerSize;
  @property
  def sBinaryPath(oProcess):
    return oProcess.oWindowsAPIProcess.sBinaryPath;
  @property
  def sBinaryName(oProcess):
    return oProcess.oWindowsAPIProcess.sBinaryName;
  @property
  def sCommandLine(oProcess):
    return oProcess.oWindowsAPIProcess.sCommandLine;
  @property
  def uIntegrityLevel(oProcess):
    return oProcess.oWindowsAPIProcess.uIntegrityLevel;
  def foGetVirtualAllocationForAddress(oSelf, uAddress):
    return oSelf.oWindowsAPIProcess.foGetVirtualAllocationForAddress(uAddress);  
  def fs0ReadStringForAddressAndLength(oSelf, uAddress, uSize, bUnicode = False):
    return oSelf.oWindowsAPIProcess.fs0ReadStringForAddressAndLength(uAddress, uSize, bUnicode);  
  def fs0ReadNullTerminatedStringForAddress(oSelf, uAddress, bUnicode = False):
    return oSelf.oWindowsAPIProcess.fs0ReadNullTerminatedStringForAddress(uAddress, bUnicode);  
  def fa0uReadBytesForAddressAndSize(oSelf, uAddress, uSize):
    return oSelf.oWindowsAPIProcess.fa0uReadBytesForAddressAndSize(uAddress, uSize);  
  def fu0ReadValueForAddressAndSize(oSelf, uAddress, uSize):
    return oSelf.oWindowsAPIProcess.fu0ReadValueForAddressAndSize(uAddress, uSize);  
  def fa0uReadValuesForAddressSizeAndCount(oSelf, uAddress, uSize, uCount):
    return oSelf.oWindowsAPIProcess.fa0uReadValuesForAddressSizeAndCount(uAddress, uSize, uCount);  
  def fu0ReadPointerForAddress(oSelf, uAddress):
    return oSelf.oWindowsAPIProcess.fu0ReadPointerForAddress(uAddress);  
  def fa0uReadPointersForAddressAndCount(oSelf, uAddress, uCount):
    return oSelf.oWindowsAPIProcess.fa0uReadPointersForAddressAndCount(uAddress, uCount);  
  def fo0ReadStructureForAddress(oSelf, cStructure, uAddress):
    return oSelf.oWindowsAPIProcess.fo0ReadStructureForAddress(cStructure, uAddress);  
  def fWriteBytesForAddress(oSelf, sData, uAddress):
    return oSelf.oWindowsAPIProcess.fWriteBytesForAddress(oSelf, sData, uAddress, bUnicode);
  def fWriteStringForAddress(oSelf, sData, uAddress, bUnicode = False):
    return oSelf.oWindowsAPIProcess.fWriteStringForAddress(oSelf, sData, uAddress, bUnicode);
  
  fEnsurePageHeapIsEnabled = cProcess_fEnsurePageHeapIsEnabled;
  fo0GetHeapManagerDataForAddress = cProcess_fo0GetHeapManagerDataForAddress;
  ftxSplitSymbolOrAddress = cProcess_ftxSplitSymbolOrAddress;
  fuGetAddressForSymbol = cProcess_fuGetAddressForSymbol;

