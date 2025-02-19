from mWindowsAPI import \
  cProcess as cWindowsAPIProcess, \
  cModule as cWindowsAPIModule, \
  fsHexNumber;
from mWindowsSDK import ERROR_ACCESS_DENIED;

from ..mModule import cModule;
from ..mDisassembler import \
  fo0GetDisassemblyForProcessStartAddressAndNumberOfBytes, \
  fo0GetDisassemblyForProcessStartAddressAndNumberOfInstructions, \
  fo0GetInstructionForProcessAndAddress, \
  fo0GetInstructionForProcessAndBeforeAddress;
from ..mExceptions import cNoAccessToProcessException;

from .cProcess_fa0txGetRegistersForThreadId import cProcess_fa0txGetRegistersForThreadId;
from .cProcess_fasbGetStack import cProcess_fasbGetStack;
from .cProcess_fEnsurePageHeapIsEnabled import cProcess_fEnsurePageHeapIsEnabled;
from .cProcess_fLoadSymbols import cProcess_fLoadSymbols;
from .cProcess_fo0GetFunctionForAddress import cProcess_fo0GetFunctionForAddress;
from .cProcess_fo0GetModuleForCdbId import cProcess_fo0GetModuleForCdbId;
from .cProcess_fo0GetPageHeapManagerDataForAddressNearHeapBlock import \
    cProcess_fo0GetPageHeapManagerDataForAddressNearHeapBlock;
from .cProcess_fo0GetWindowsHeapManagerDataForAddressNearHeapBlock import \
    cProcess_fo0GetWindowsHeapManagerDataForAddressNearHeapBlock;
from .cProcess_fs0GetDetailsForAddress import cProcess_fs0GetDetailsForAddress;
from .cProcess_fsb0GetSymbolForAddress import cProcess_fsb0GetSymbolForAddress;
from .cProcess_ftxSplitSymbolOrAddress import cProcess_ftxSplitSymbolOrAddress;
from .cProcess_fu0GetTargetAddressForCallInstructionReturnAddress import \
    cProcess_fu0GetTargetAddressForCallInstructionReturnAddress;
from .cProcess_fu0GetAddressForSymbol import cProcess_fu0GetAddressForSymbol;

gbDebugOutput = False;

class cProcess(object):
  def __init__(oSelf, oCdbWrapper, uId):
    oSelf.oCdbWrapper = oCdbWrapper;
    oSelf.uId = uId;
    oSelf.bTerminated = False; # Will be set to True by `cCdbWrapper_fHandleCurrentApplicationProcessTermination` once terminated
    
    # Modules will be cached here. They are discarded whenever the application is resumed.
    oSelf.__d0oModule_by_uStartAddress = None;
    
    # We'll try to determine if page heap is enabled for every process. However, this may not always work. So until
    # we've successfully found out, the following value will be None. Once we know, it is set to True or False.
    oSelf.bPageHeapEnabled = None;
    
    # Process Information is only determined when needed and cached.
    oSelf.__oWindowsAPIProcess = None; 
    
    # Symbols and heap manager data for addresses will be cached here. They are discarded whenever the application is resumed.
    oSelf.bSymbolsLoaded = False;
    oSelf.__dsb0Symbol_by_uAddress = {};
    oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock = {};
    
  @property
  def oWindowsAPIProcess(oSelf):
    if oSelf.__oWindowsAPIProcess is None:
      try:
        oSelf.__oWindowsAPIProcess = cWindowsAPIProcess(oSelf.uId);
      except OSError as oError:
        if oError.errno == ERROR_ACCESS_DENIED:
          raise cNoAccessToProcessException(oSelf.uId);
        else:
          raise;
    return oSelf.__oWindowsAPIProcess;
  
  def foGetWindowsAPIThreadForId(oSelf, uThreadId):
    return oSelf.oWindowsAPIProcess.foGetThreadForId(uThreadId);
  
  @property
  def sSimplifiedBinaryName(oSelf):
    # Windows filesystems are case-insensitive and the casing of the binary name may change between versions.
    # Lowercasing the name prevents this from resulting in location ids that differ in casing while still returning
    # a name that can be used to access the file.
    return oSelf.sBinaryName.lower();
  
  @property
  def oMainModule(oSelf):
    uMainModuleStartAddress = oSelf.oWindowsAPIProcess.uBinaryStartAddress;
    o0MainModule = oSelf.doModule_by_uStartAddress.get(uMainModuleStartAddress);
    assert o0MainModule, \
          "Cannot find main module for binary start address 0x%X!?" % uMainModuleStartAddress;
    return o0MainModule;
  
  def fo0GetModuleForStartAddress(oSelf, uStartAddress):
    return oSelf.doModule_by_uStartAddress.get(uStartAddress);
  
  @property
  def doModule_by_uStartAddress(oSelf):
    if oSelf.__d0oModule_by_uStartAddress is None:
      oSelf.__d0oModule_by_uStartAddress = {};
      for oWindowsAPIModule in cWindowsAPIModule.faoGetForProcessId(oSelf.uId):
        # This list contains all modules, even 64-bit WoW64 modules loaded in
        # a 32-bit process. cdb.exe does not process these, so we'll ignore them
        # too (until we've gotten rid of cdb.exe entirely).
        oSelf.__d0oModule_by_uStartAddress[oWindowsAPIModule.uStartAddress] = \
            cModule(oSelf, oWindowsAPIModule);
    return oSelf.__d0oModule_by_uStartAddress;
  
  @property
  def aoModules(oSelf):
    return list(oSelf.doModule_by_uStartAddress.values());
  
  def fClearCache(oSelf):
    # Assume that all modules can be unloaded, except the main module.
    oSelf.__d0oModule_by_uStartAddress = None;
    oSelf.__dsb0Symbol_by_uAddress = {};
    oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock = {};
  
  def fSelectInCdb(oSelf):
    oSelf.oCdbWrapper.fSelectProcessId(oSelf.uId);
  
  def __str__(oSelf):
    return 'Process(%s %s #%d)' % (oSelf.sBinaryName, oSelf.sISA, oSelf.uProcessId);
  
  def fuAddBreakpointForAddress(oSelf, uAddress, fCallback, u0ThreadId = None, sb0Command = None):
    return oSelf.oCdbWrapper.fuAddBreakpointForProcessIdAndAddress(
      uProcessId = oSelf.uId,
      uAddress = uAddress,
      fCallback = fCallback,
      u0ThreadId = u0ThreadId,
      sb0Command = sb0Command,
    );
  
  def fasbExecuteCdbCommand(oSelf, sbCommand, sb0Comment, **dxArguments):
    # Make sure all commands send to cdb are send in the context of this process.
    oSelf.fSelectInCdb();
    return oSelf.oCdbWrapper.fasbExecuteCdbCommand(sbCommand, sb0Comment, **dxArguments);
  
  def fuGetValueForRegister(oSelf, sbRegister, sb0Comment):
    oSelf.fSelectInCdb();
    return oSelf.oCdbWrapper.fuGetValueForRegister(sbRegister, sb0Comment);
  def fuGetValueForStackPointer(oSelf):
    return oSelf.fuGetValueForRegister(
      {"x86": b"esp", "x64": b"rsp"}[oSelf.sISA],
      b"Determining stack pointer value",
  );
  def fuGetValueForInstructionPointer(oSelf):
    return oSelf.fuGetValueForRegister(
      {"x86": b"eip", "x64": b"rip"}[oSelf.sISA],
      b"Determining instruction pointer value",
    );
  
  # Proxy properties and methods to oWindowsAPIProcess
  @property
  def sISA(oSelf):
    return oSelf.oWindowsAPIProcess.sISA;
  @property
  def uPointerSizeInBits(oSelf):
    return oSelf.oWindowsAPIProcess.uPointerSizeInBits;
  @property
  def uPointerSizeInBytes(oSelf):
    return oSelf.oWindowsAPIProcess.uPointerSizeInBytes;
  # This one is to be deprecated because it is ambiguous about the unit.
  @property
  def uPointerSize(oSelf):
    return oSelf.oWindowsAPIProcess.uPointerSize;
  @property
  def sBinaryPath(oSelf):
    return oSelf.oWindowsAPIProcess.sBinaryPath;
  @property
  def sBinaryName(oSelf):
    return oSelf.oWindowsAPIProcess.sBinaryName;
  @property
  def sCommandLine(oSelf):
    return oSelf.oWindowsAPIProcess.sCommandLine;
  @property
  def uIntegrityLevel(oSelf):
    return oSelf.oWindowsAPIProcess.uIntegrityLevel;
  def fo0GetVirtualAllocationForAddress(oSelf, uAddress):
    return oSelf.oWindowsAPIProcess.fo0GetVirtualAllocationForAddress(uAddress);  
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
    return oSelf.oWindowsAPIProcess.fWriteBytesForAddress(oSelf, sData, uAddress);
  def fWriteStringForAddress(oSelf, sData, uAddress, bUnicode = False):
    return oSelf.oWindowsAPIProcess.fWriteStringForAddress(oSelf, sData, uAddress, bUnicode);
  
  def fo0GetHeapManagerDataForAddressNearHeapBlock(oSelf, uAddressNearHeapBlock):
    # Wrap this in a bit of caching for speed.
    if uAddressNearHeapBlock in oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock:
      return oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock[uAddressNearHeapBlock];
    if oSelf.bPageHeapEnabled:
      return oSelf.fo0GetPageHeapManagerDataForAddressNearHeapBlock(uAddressNearHeapBlock);
    else:
      return oSelf.fo0GetWindowsHeapManagerDataForAddressNearHeapBlock(uAddressNearHeapBlock);
  def fo0GetPageHeapManagerDataForAddressNearHeapBlock(oSelf, uAddressNearHeapBlock):
    # Wrap this in a bit of caching for speed.
    if uAddressNearHeapBlock not in oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock:
      oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock[uAddressNearHeapBlock] = \
          cProcess_fo0GetPageHeapManagerDataForAddressNearHeapBlock(oSelf, uAddressNearHeapBlock);
    return oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock[uAddressNearHeapBlock];
  def fo0GetWindowsHeapManagerDataForAddressNearHeapBlock(oSelf, uAddressNearHeapBlock):
    # Wrap this in a bit of caching for speed.
    if uAddressNearHeapBlock not in oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock:
      oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock[uAddressNearHeapBlock] = \
          cProcess_fo0GetWindowsHeapManagerDataForAddressNearHeapBlock(oSelf, uAddressNearHeapBlock);
    return oSelf.__do0HeapManagerData_by_uAddressNearHeapBlock[uAddressNearHeapBlock];

  def fsb0GetSymbolForAddress(oSelf, uAddress, sbAddressDescription):
    # Wrap this in a bit of caching for speed.
    if uAddress in oSelf.__dsb0Symbol_by_uAddress:
      return oSelf.__dsb0Symbol_by_uAddress[uAddress];
    sb0Symbol = cProcess_fsb0GetSymbolForAddress(oSelf, uAddress, sbAddressDescription);
    oSelf.__dsb0Symbol_by_uAddress[uAddress] = sb0Symbol;
    return sb0Symbol;
  
  def fo0GetDisassemblyForStartAddressAndNumberOfBytes(oSelf, uStartAddress, uNumberOfBytes):
    return fo0GetDisassemblyForProcessStartAddressAndNumberOfBytes(
      oProcess = oSelf,
      uStartAddress = uStartAddress,
      uNumberOfBytes = uNumberOfBytes,
    );
  def fo0GetDisassemblyForStartAddressAndNumberOfInstructions(oSelf, uStartAddress, uNumberOfInstructions):
    return fo0GetDisassemblyForProcessStartAddressAndNumberOfInstructions(
      oProcess = oSelf,
      uStartAddress = uStartAddress,
      uNumberOfInstructions = uNumberOfInstructions,
    );
  def fo0GetInstructionForAddress(oSelf, uAddress):
    return fo0GetInstructionForProcessAndAddress(
      oProcess = oSelf,
      uAddress = uAddress,
    );
  def fo0GetInstructionBeforeAddress(oSelf, uAddress):
    return fo0GetInstructionForProcessAndBeforeAddress(
      oProcess = oSelf,
      uAddress = uAddress,
    );

  fa0txGetRegistersForThreadId = cProcess_fa0txGetRegistersForThreadId;
  fasbGetStack = cProcess_fasbGetStack;
  fEnsurePageHeapIsEnabled = cProcess_fEnsurePageHeapIsEnabled;
  fLoadSymbols = cProcess_fLoadSymbols;
  fo0GetFunctionForAddress = cProcess_fo0GetFunctionForAddress;
  fo0GetModuleForCdbId = cProcess_fo0GetModuleForCdbId;
  ftxSplitSymbolOrAddress = cProcess_ftxSplitSymbolOrAddress;
  fu0GetTargetAddressForCallInstructionReturnAddress = cProcess_fu0GetTargetAddressForCallInstructionReturnAddress;
  fu0GetAddressForSymbol = cProcess_fu0GetAddressForSymbol;
  fs0GetDetailsForAddress = cProcess_fs0GetDetailsForAddress;

