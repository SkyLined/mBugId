import os, re;
from cModule import cModule;
from cProcess_fauGetBytes import cProcess_fauGetBytes;
from cProcess_fEnsurePageHeapIsEnabled import cProcess_fEnsurePageHeapIsEnabled;
from cProcess_fsGet_String import cProcess_fsGetASCIIString, cProcess_fsGetUnicodeString;
from cProcess_ftxSplitSymbolOrAddress import cProcess_ftxSplitSymbolOrAddress;
from cProcess__fuGetIntegrityLevel import cProcess__fuGetIntegrityLevel;
from cProcess_fuGetValue import cProcess_fuGetValue;
from cProcess_fuGetValueForRegister import cProcess_fuGetValueForRegister;

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
    
    # oProcess.sBasePath is only determined when needed and cached using __fGetProcessInformation
    oProcess.__sBasePath = None;
    
    # oProcess.sCommandLine is only determined when needed and cached using __fGetProcessInformation
    oProcess.__sCommandLine = None; 
    
    # oProcess.sISA is only determined when needed and cached using __fGetProcessInformation
    oProcess.__sISA = None; 
    
    # oProcess.uPointerSize is only determined when needed and cached using __fGetProcessInformation
    oProcess.__uPointerSize = None; # 
    
    # oProcess.uPageSize is only determined when needed and cached
    oProcess.__uPageSize = None;
    
    # oProcess.oMainModule is only determined when needed and cached
    oProcess.__oMainModule = None; # .oMainModule is JIT
    # In order to determine oProcess.oMainModule, we need it's base address. This is set by __fGetProcessInformation
    oProcess.__uMainModuleImageBaseAddress = None;
    
    # oProcess.aoModules is only determined when needed; it creates an entry in __doModules_by_sCdbId for every loaded
    # module and returns all the values in the first dict. Since this dict is cached, this only needs to be done once
    # until the cache is invalidated.
    oProcess.__bAllModulesEnumerated = False;
  
  @property
  def sBinaryName(oProcess):
    return oProcess.oMainModule.sBinaryName;
  
  @property
  def sBasePath(oProcess):
    if oProcess.__sBasePath is None:
      oProcess.__fGetProcessInformation();
    return oProcess.__sBasePath;
  
  @property
  def sCommandLine(oProcess):
    if oProcess.__sCommandLine is None:
      oProcess.__fGetProcessInformation();
    return oProcess.__sCommandLine;
  
  @property
  def sISA(oProcess):
    if oProcess.__sISA is None:
      oProcess.__fGetProcessInformation();
    return oProcess.__sISA;
  
  @property
  def uPointerSize(oProcess):
    if oProcess.__uPointerSize is None:
      oProcess.__fGetProcessInformation();
    return oProcess.__uPointerSize;
  
  @property
  def uPageSize(oProcess):
    if oProcess.__uPageSize is None:
      oProcess.__uPageSize = oProcess.fuGetValueForRegister("$pagesize", "Get page size for process");
    return oProcess.__uPageSize;
  
  @property
  def uIntegrityLevel(oProcess):
    # JIT with cache
    try:
      return oProcess.__uIntegrityLevel;
    except:
      oProcess.__uIntegrityLevel = cProcess__fuGetIntegrityLevel(oProcess);
      return oProcess.__uIntegrityLevel;
  
  def __fGetProcessInformation(oProcess):
    # We want to know the main module, i.e. the binary for this process and the Instruction Set Architecture for this
    # process (i.e. x86 or x64).
    asPEBOutput = oProcess.fasExecuteCdbCommand(
      sCommand = "!peb;",
      sComment = "Get current proces environment block",
      bRetryOnTruncatedOutput = True,
      srIgnoreErrors = r".*",
    );
    # Sample output:
    # |Wow64 PEB32 at 34c000
    # |    InheritedAddressSpace:    No
    # |    ReadImageFileExecOptions: No
    # |    BeingDebugged:            Yes
    # |    ImageBaseAddress:         0000000000400000
    # |    Ldr                       0000000077227c00
    # |    ***  _PEB_LDR_DATA type was not found...
    # |    *** unable to read Ldr table at 0000000077227c00
    # |    SubSystemData:     0000000000000000
    # |    ProcessHeap:       0000000004d90000
    # |    ProcessParameters: 0000000004db34d8
    # |    ***  _CURDIR type was not found...
    # |    WindowTitle:  \'&lt; Name not readable &gt;\'
    # |    ImageFile:    \'&lt; Name not readable &gt;\'
    # |    CommandLine:  \'&lt; Name not readable &gt;\'
    # |    DllPath:      \'&lt; Name not readable &gt;\'
    # |    Environment:  0000000000000000
    # |       Unable to read Environment string.
    # |Wow64 PEB at 000000000034b000
    # |    InheritedAddressSpace:    No
    # |    ReadImageFileExecOptions: No
    # |    BeingDebugged:            Yes
    # |    ImageBaseAddress:         0000000000400000
    # |    Ldr                       00007ffd6377b340
    # |    *** unable to read Ldr table at 00007ffd6377b340
    # |    SubSystemData:     0000000000000000
    # |    ProcessHeap:       0000000001cd0000
    # |    ProcessParameters: 0000000001d4e840
    # ...
    #
    # |PEB at 00000058c6282000
    # |error 1 InitTypeRead( nt!_PEB at 00000058c6282000)...
    uPEBAddress = None;
    for sLine in asPEBOutput:
      if uPEBAddress is None:
        # First look for the (32-bit) PEB address:
        oPEBMatch = re.match(r"^(Wow64 PEB32|PEB) at ([0-9a-f]+)$", sLine, re.I);
        if oPEBMatch:
          sPEBType, sPEBAddress = oPEBMatch.groups();
          uPEBAddress = long(sPEBAddress, 16);
          # This seems to work well enough, but an alternative way to determine the pointer size is to check if the
          # PEB address string consists of 16 hex digits (64-bits) or less (32-bits) similar to how it is done in
          # cThreadEnvironmentBlock at the moment of this writing.
          uPEBPointerSize = sPEBType == "Wow64 PEB32" or oProcess.oCdbWrapper.sCdbISA == "x86" and 4 or 8;
      elif oProcess.__uMainModuleImageBaseAddress is None:
        # Then look for the ImageBaseAddress:
        oImageBaseAddressMatch = re.match(r"^    ImageBaseAddress:\s+([0-9a-f]+)$", sLine, re.I);
        if oImageBaseAddressMatch:
          oProcess.__uMainModuleImageBaseAddress = long(oImageBaseAddressMatch.group(1), 16);
      else:
        oImageFileMatch = re.match(r"^    ImageFile:\s+'(.*)'$", sLine, re.I);
        if oImageFileMatch:
          oProcess.__sBasePath = os.path.dirname(oImageFileMatch.group(1));
        else:
          oCommandLineMatch = re.match(r"^    CommandLine:\s+'(.*)'$", sLine, re.I);
          if oCommandLineMatch:
            oProcess.__sCommandLine = oCommandLineMatch.group(1);
            break;
    else:
      # The PEB address should always be output on the first line (though there may be some NatVis cruft before it,
      # which we'll ignore). If it's not, that is an error.
      assert uPEBAddress is not None, \
          "No PEB information in !peb output:\r\n%s" % "\r\n".join(asPEBOutput);
      # The ImageBaseAddress was not provided by !peb, so we'll have to determine what it is ourselves:
      # The PEB has a pointer to the main modules base address (ImageBaseAddress):
      # typedef struct _PEB
      # {
      #     UCHAR InheritedAddressSpace;
      #     UCHAR ReadImageFileExecOptions;
      #     UCHAR BeingDebugged;
      #     UCHAR BitField;
      #     // 4 bytes of padding will be inserted on x64 to align it to the pointer size.
      #     PVOID Mutant;
      #     PVOID ImageBaseAddress;     <=== That's what we're looking for.
      #     PPEB_LDR_DATA Ldr;
      oProcess.__uMainModuleImageBaseAddress = oProcess.fuGetValue(
        "poi(0x%X)" % (uPEBAddress + 2 * uPEBPointerSize),
        "Get main module image base from PEB"
      );
    # I've not found a very reliable way of determining the ISA for the process, other than to assume x86 processes
    # always load all their modules at addresses with the top 32 bits set to 0, and x64 processes always load their
    # modules at addresses with at least one of the upper 32 bits set. Let me know if this is wrong, preferably with
    # an improved way of detecting the ISA of the process.
    oProcess.__sISA = oProcess.__uMainModuleImageBaseAddress < (1 << 32) and "x86" or "x64";
    oProcess.__uPointerSize = {"x64": 8, "x86": 4}[oProcess.sISA];
  
  @property
  def oMainModule(oProcess):
    if oProcess.__oMainModule is None:
      if oProcess.__uMainModuleImageBaseAddress is None:
        # Get information from the PEB about the location of the main module:
        oProcess.__fGetProcessInformation();
      oProcess.__oMainModule = oProcess.foGetOrCreateModuleForStartAddress(oProcess.__uMainModuleImageBaseAddress);
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
  
  def fuAddBreakpoint(oProcess, uAddress, fCallback, uThreadId = None, sCommand = None):
    return oProcess.oCdbWrapper.fuAddBreakpoint(
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
  def fsGetSymbolForAddress(oProcess, sAddress, sComment):
    return cCdbWrapper_fsGetSymbolForAddress(oProcess, sAddress, sComment);
  def fsGetASCIIString(oProcess, sAddress, sComment):
    return cProcess_fsGetASCIIString(oProcess, sAddress, sComment);
  def fsGetUnicodeString(oProcess, sAddress, sComment):
    return cProcess_fsGetUnicodeString(oProcess, sAddress, sComment);
  def fauGetBytes(oCdbWrapper, uAddress, uSize, sComment):
    return cProcess_fauGetBytes(oCdbWrapper, uAddress, uSize, sComment);
  
