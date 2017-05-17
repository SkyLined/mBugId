import os, re;
from cModule import cModule;
from cProcess_ftxSplitSymbolOrAddress import cProcess_ftxSplitSymbolOrAddress;
from cProcess_fEnsurePageHeapIsEnabled import cProcess_fEnsurePageHeapIsEnabled;

class cProcess(object):
  def __init__(oProcess, oCdbWrapper, uId):
    oProcess.oCdbWrapper = oCdbWrapper;
    oProcess.uId = uId;
    oProcess.__uPageSize = None;
    oProcess.bNew = True; # Will be set to False by .fCdbStdInOutThread once application is run again.
    oProcess.bTerminated = False; # Will be set to True by .foSetCurrentProcessAfterApplicationRan once process is terminated
    oProcess.__doModules_by_sCdbId = {};
    
    oProcess.bPageHeapEnabled = None; # Set to True or False when we find out later.
    
    oProcess.__sISA = None; # .sISA is JIT using __fGetProcessInformation
    oProcess.__uPointerSize = None; # .uPointerSize is JIT using __fGetProcessInformation
    
    oProcess.__oMainModule = None; # .oMainModule is JIT
    oProcess.__uMainModuleImageBaseAddress = None; # Required for .oMainModule JIT code, set by __fGetProcessInformation
  
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
  
  def __fGetProcessInformation(oProcess):
    # We want to know the main module, i.e. the binary for this process and the Instruction Set Architecture for this
    # process (i.e. x86 or x64).
    asPEBOutput = oProcess.oCdbWrapper.fasSendCommandAndReadOutput("!peb; $$ Get current proces environment block");
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
          uPEBPointerSize = sPEBType == "Wow64 PEB32" or oProcess.oCdbWrapper.sCdbISA == "x86" and 4 or 8;
      elif oProcess.__uMainModuleImageBaseAddress is None:
        # Then look for the ImageBaseAddress:
        oImageBaseAddressMatch = re.match(r"^    ImageBaseAddress:\s+([0-9a-f]+)$", sLine, re.I);
        if oImageBaseAddressMatch:
          oProcess.__uMainModuleImageBaseAddress = long(oImageBaseAddressMatch.group(1), 16);
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
      oProcess.__uMainModuleImageBaseAddress = oProcess.oCdbWrapper.fuGetValue(
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
      asModuleInformationOutput = oProcess.oCdbWrapper.fasSendCommandAndReadOutput("lmn a 0x%X; $$ Get module cdb id" % oProcess.__uMainModuleImageBaseAddress);
      # Sample output:
      # |0:007> lmn a 7ff6a8870000
      # |start             end                 module name
      # |00007ff6`a8870000 00007ff6`a88b1000   notepad  notepad.exe
      assert len(asModuleInformationOutput) == 2, \
          "Unexpected number of lines in module information:\r\n%s" % "\r\n".join(asModuleInformationOutput);
      assert re.match(r"^start\s+end\s+module name\s*$", asModuleInformationOutput[0]), \
          "Unexpected module information header:\r\n%s" % "\r\n".join(asModuleInformationOutput);
      oModuleInformationMatch = re.match("^([0-9`a-f]+)\s+([0-9`a-f]+)\s+(\w+)\s+.*$", asModuleInformationOutput[1], re.I);
      assert oModuleInformationMatch, \
          "Unexpected module information:\r\n%s" % "\r\n".join(asModuleInformationOutput);
      (sStartAddress, sEndAddress, sMainModuleCdbId) = oModuleInformationMatch.groups();
      uStartAddress = long(sStartAddress.replace("`", ""), 16)
      assert uStartAddress == oProcess.__uMainModuleImageBaseAddress, \
          "Two different base addresses returned for module: %X and %X" % (uStartAddress, oProcess.__uMainModuleImageBaseAddress);
      uEndAddress = long(sEndAddress.replace("`", ""), 16);
      oProcess.__oMainModule = cModule(oProcess, sMainModuleCdbId, uStartAddress, uEndAddress);
      oProcess.__doModules_by_sCdbId[sMainModuleCdbId] = oProcess.oMainModule;
    return oProcess.__oMainModule;
  
  @property
  def sBinaryName(oProcess):
    return oProcess.oMainModule.sBinaryName;
  
  @property
  def uPageSize(oProcess):
    if oProcess.__uPageSize is None:
      oProcess.fSelectInCdb();
      oProcess.__uPageSize = oProcess.fuGetValue("@$pagesize", "Get page size for process");
    return oProcess.__uPageSize;
  
  def fClearCache(oProcess):
    # Assume that all modules can be unloaded, except the main module.
    oProcess.__doModules_by_sCdbId = {oProcess.oMainModule.sCdbId: oProcess.oMainModule};
  
  def foGetOrCreateModuleForCdbId(oProcess, sCdbId, *axAddressArguments, **dxAddressArguments):
    oProcess.oMainModule; # Make sure we've already created the main module, or it could be created twice.
    if sCdbId not in oProcess.__doModules_by_sCdbId:
      oProcess.__doModules_by_sCdbId[sCdbId] = cModule(oProcess, sCdbId, *axAddressArguments, **dxAddressArguments);
    return oProcess.__doModules_by_sCdbId[sCdbId];
  
  def fSelectInCdb(oProcess):
    oProcess.oCdbWrapper.fSelectProcess(oProcess.uId);
  
  def fuGetValue(oProcess, sValueName, sComment):
    oCdbWrapper = oProcess.oCdbWrapper;
    oProcess.fSelectInCdb();
    uValue = oCdbWrapper.fuGetValue(sValueName, sComment);
    return uValue;
  
  def __str__(oProcess):
    return 'Process(%s %s #%d)' % (oProcess.sBinaryName, oProcess.sISA, oProcess.uProcessId);
  
  def ftxSplitSymbolOrAddress(oProcess, sSymbolOrAddress):
    return cProcess_ftxSplitSymbolOrAddress(oProcess, sSymbolOrAddress);
  
  def fEnsurePageHeapIsEnabled(oProcess):
    return cProcess_fEnsurePageHeapIsEnabled(oProcess);