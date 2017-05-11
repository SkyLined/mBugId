import os, re;
from cModule import cModule;
from cProcess_ftxSplitSymbolOrAddress import cProcess_ftxSplitSymbolOrAddress;
from cProcess_fEnsurePageHeapIsEnabled import cProcess_fEnsurePageHeapIsEnabled;

class cProcess(object):
  def __init__(oProcess, oCdbWrapper, uId):
    oProcess.oCdbWrapper = oCdbWrapper;
    oProcess.uId = uId;
    oProcess.__sMainModuleCdbId = None;
    oProcess.__uPointerSize = None;
    oProcess.__uPageSize = None;
    oProcess.bNew = True; # Will be set to False by .fCdbStdInOutThread once application is run again.
    oProcess.bTerminated = False; # Will be set to True by .foSetCurrentProcessAfterApplicationRan once process is terminated
    oProcess.__doModules_by_sCdbId = {};
    oProcess.bPageHeapEnabled = None; # We do not know yet.
  
  @property
  def oMainModule(oProcess):
    if oProcess.__sMainModuleCdbId:
      return oProcess.foGetOrCreateModuleForCdbId(oProcess.__sMainModuleCdbId);
    # We want to know the main module, i.e. the binary for this process. We can find it as the first entry in the 
    # InLoadOrderModuleList in the PEB:
    oCdbWrapper = oProcess.oCdbWrapper;
    oProcess.fSelectInCdb();
    asCurrentPEBOutput = oCdbWrapper.fasSendCommandAndReadOutput("!peb; $$ Get current proces environment block");
    # Sample output:
    # |PEB at 0000004a19376000
    # ... (for N-bit process running on N-bit windows (x86 on x86 or x64 on x64)
    # or
    # |Wow64 PEB32 at 377000
    # ... (for x86 process running on x64 windows)
    # the following status messages may precede the output and can safely be ignored AFAICT.
    # |NatVis at "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\Visualizers\\atlmfc.natvis" is already loaded.  Skipping...
    # |NatVis at "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\Visualizers\\concurrency.natvis" is already loaded.  Skipping...
    # |NatVis at "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\Visualizers\\cpp_rest.natvis" is already loaded.  Skipping...
    # |NatVis at "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\Visualizers\\Kernel.natvis" is already loaded.  Skipping...
    # |NatVis at "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\Visualizers\\stl.natvis" is already loaded.  Skipping...
    # |NatVis at "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\Visualizers\\Windows.Data.Json.natvis" is already loaded.  Skipping...
    # |NatVis at "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\Visualizers\\Windows.Devices.Geolocation.natvis" is already loaded.  Skipping...
    # Also, it has been known to crash:
    # |Non-command exception C0000005 at 00007ffd`104c7dfe in command filter
    # |c0000005 Exception in exts.peb debugger extension.
    # |      PC: 00007ffd`104c7dfe  VA: 00000000`0000000c  R/W: 0  Parameter: 00000000`00000000
    # This is currently not handled, as it is not very common and I don't know how to handle it anyway.
    uPEBAddressIndex = 0;
    while uPEBAddressIndex < len(asCurrentPEBOutput) and re.match('NatVis at ".+" is already loaded\.  Skipping...$', asCurrentPEBOutput[uPEBAddressIndex]):
      uPEBAddressIndex += 1;
    assert uPEBAddressIndex < len(asCurrentPEBOutput), \
        "Missing PEB address output!\r\n%s" % "\r\n".join(asCurrentPEBOutput);
    oPEBAddressMatch = re.match(r"^(?:PEB|Wow64 PEB32) at ([0-9a-f]+)\s*$", asCurrentPEBOutput[uPEBAddressIndex], re.I);
    assert oPEBAddressMatch, \
        "Unrecognized PEB address output: %s\r\n%s" % (repr(asCurrentPEBOutput[uPEBAddressIndex]), "\r\n".join(asCurrentPEBOutput));
    uPEBAddress = long(oPEBAddressMatch.group(1), 16);
    # The PEB has a pointer to the main modules base address (ImageBaseAddress):
    # typedef struct _PEB
    # {
    #     UCHAR InheritedAddressSpace;
    #     UCHAR ReadImageFileExecOptions;
    #     UCHAR BeingDebugged;
    #     UCHAR BitField;
    #     PVOID Mutant;
    #     PVOID ImageBaseAddress;
    #     PPEB_LDR_DATA Ldr;
    uImageBaseAddressAddress = uPEBAddress + 2 * oProcess.uPointerSize;
    uImageBaseAddress = oCdbWrapper.fuGetValue("poi(0x%X)" % uImageBaseAddressAddress);
    asModuleCdbIdOutput = oCdbWrapper.fasSendCommandAndReadOutput("lmn a 0x%X; $$ Get module cdb id" % uImageBaseAddress);
    # Sample output:
    # |0:007> lmn a 7ff6a8870000
    # |start             end                 module name
    # |00007ff6`a8870000 00007ff6`a88b1000   notepad  notepad.exe
    assert len(asModuleCdbIdOutput) == 2, \
        "Unexpected number of lines in module information:\r\n%s" % "\r\n".join(asModuleCdbIdOutput);
    assert re.match(r"^start\s+end\s+module name\s*$", asModuleCdbIdOutput[0]), \
        "Unexpected module information header:\r\n%s" % "\r\n".join(asModuleCdbIdOutput);
    oStartAddressEndAddressAndCdbIdMatch = re.match("^([0-9`a-f]+)\s+([0-9`a-f]+)\s+(\w+)\s+.*$", asModuleCdbIdOutput[1], re.I);
    assert oStartAddressEndAddressAndCdbIdMatch, \
        "Unexpected module information:\r\n%s" % "\r\n".join(asModuleCdbIdOutput);
    (sStartAddress, sEndAddress, sCdbId) = oStartAddressEndAddressAndCdbIdMatch.groups();
    uStartAddress = long(sStartAddress.replace("`", ""), 16)
    assert uStartAddress == uImageBaseAddress, \
        "Two different base addresses returned for module: %X and %X" % (uStartAddress, uImageBaseAddress);
    uEndAddress = long(sEndAddress.replace("`", ""), 16);
    oProcess.__sMainModuleCdbId = sCdbId;
    oMainModule = cModule(oProcess, sCdbId, uStartAddress, uEndAddress);
    oProcess.__doModules_by_sCdbId[sCdbId] = oMainModule;
    return oMainModule;
  
  @property
  def sBinaryName(oProcess):
    return oProcess.oMainModule.sBinaryName;
  
  @property
  def uPointerSize(oProcess):
    if oProcess.__uPointerSize is None:
      oProcess.__uPointerSize = oProcess.fuGetValue("@$ptrsize");
    return oProcess.__uPointerSize;
  
  @property
  def uPageSize(oProcess):
    if oProcess.__uPageSize is None:
      oProcess.__uPageSize = oProcess.fuGetValue("@$pagesize");
    return oProcess.__uPageSize;
  
  def fClearCache(oProcess):
    # Assume that all modules can be unloaded, except the main binary.
    oMainModule = oProcess.__doModules_by_sCdbId.get(oProcess.__sMainModuleCdbId);
    oProcess.__doModules_by_sCdbId = {};
    if oMainModule:
      oProcess.__doModules_by_sCdbId[oProcess.__sMainModuleCdbId] = oMainModule;
  
  def foGetOrCreateModuleForCdbId(oProcess, sCdbId, *axAddressArguments, **dxAddressArguments):
    if sCdbId not in oProcess.__doModules_by_sCdbId:
      oProcess.__doModules_by_sCdbId[sCdbId] = cModule(oProcess, sCdbId, *axAddressArguments, **dxAddressArguments);
    return oProcess.__doModules_by_sCdbId[sCdbId];
  
  def fSelectInCdb(oProcess):
    oCdbWrapper = oProcess.oCdbWrapper;
    oCdbWrapper.fSelectProcess(oProcess.uId);
  
  def fuGetValue(oProcess, sValueName):
    oCdbWrapper = oProcess.oCdbWrapper;
    oProcess.fSelectInCdb();
    uValue = oCdbWrapper.fuGetValue(sValueName);
    return uValue;
  
  def __str__(oProcess):
    return 'Process(%s #%d)' % (oProcess.sBinaryName, oProcess.uProcessId);
  
  def ftxSplitSymbolOrAddress(oProcess, sSymbolOrAddress):
    return cProcess_ftxSplitSymbolOrAddress(oProcess, sSymbolOrAddress);
  
  def fEnsurePageHeapIsEnabled(oProcess):
    return cProcess_fEnsurePageHeapIsEnabled(oProcess);