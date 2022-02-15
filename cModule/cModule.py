import os, re;

from ..cFunction import cFunction;
from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..mCP437 import fsCP437FromBytesString, fsCP437HTMLFromBytesString, fsCP437HTMLFromString;

grb_dlls_ErrorHeader = re.compile(
  rb'^ERROR: Could not read module list head at \w+$'
);
grb_dlls_OutputLine = re.compile(
  rb"^\s*"
  rb"0x"
  rb"[0-9`a-f]+"
  rb": "
  rb"([A-Za-z]:\\.+)"
  rb"\s*$"
);
grb_lm_Header = re.compile(
  rb"^\s*"
  rb"start"
  rb"\s+"
  rb"end"
  rb"\s+"
  rb"module name"
  rb"\s*$"
);

def ftxParse_lm_OutputAddresssesCdbIdAndSymbolStatus(sb_lm_OutputLine):
  oInformationMatch = re.match(
    rb"^\s*%s\s*$" % rb"\s+".join([
      rb"([0-9a-f`]+)",             # (start_address)
      rb"([0-9a-f`]+)",             # (end_address)
      rb"(\w+)(?:\s+\w+)?",         # (cdb_module_id) [ space char ] # char can be "C" or "T" - no idea what it means
      rb"\((deferred|(?:export|no|(?:private )?pdb) symbols)\)", # "(" (symbol_status) " symbols)"
      rb".*?",                      # symbol information.
    ]),
    sb_lm_OutputLine,
    re.I
  );
  assert oInformationMatch, \
      "Unrecognized module basic information output: %s" % sb_lm_OutputLine;
  (sbStartAddress, sbEndAddress, sbCdbId, sbSymbolStatus) = oInformationMatch.groups();
  uStartAddress = fu0ValueFromCdbHexOutput(sbStartAddress);
  uEndAddress = fu0ValueFromCdbHexOutput(sbEndAddress);
  return (uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus);

class cModule(object):
  def __init__(oSelf, oProcess, uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus):
    oSelf.oProcess = oProcess;
    oSelf.uStartAddress = uStartAddress;
    oSelf.uEndAddress = uEndAddress;
    oSelf.sbCdbId = sbCdbId;
    oSelf.__sbSymbolStatus = sbSymbolStatus; # Not exposed; use bSymbolsAvailable
    oSelf.__bSymbolLoadingFailed = False;
    # __fzGetModuleSymbolAndVersionInformation needs only be called once:
    oSelf.__bModuleSymbolAndVersionInformationAvailable = False; # set to false when __fzGetModuleSymbolAndVersionInformation is called.
    oSelf.__bBinaryPathSet = False;
    oSelf.__s0BinaryPath = None;
# We no longer track the ASCII version of binary path and name
#    oSelf.__sb0BinaryPath = None;
#    oSelf.__sb0BinaryName = None;
    oSelf.__sb0FileVersion = None;
    oSelf.__sb0Timestamp = None;
    oSelf.__doFunction_by_sbSymbol = {};
    oSelf.__atsbModuleInformationNameAndValuePairs = None;
    oSelf.sISA = oProcess.sISA; # x86/x64 processes are assumed to only load x86/x64 modules respectively.
  
  def __repr__(oSelf):
    return "<cBugId.cModule (process 0x%X, address=%X-%X, cdb id=%s, symbols=%s, binary=%s)>(#%X)" % (
      oSelf.oProcess.uId,
      oSelf.uStartAddress, oSelf.uEndAddress,
      oSelf.sbCdbId,
      oSelf.__sbSymbolStatus,
      (oSelf.__s0BinaryPath or "<unknown>") if oSelf.__bBinaryPathSet else "<tbd>",
      id(oSelf),
    );
  
  def foGetOrCreateFunctionForSymbol(oSelf, sbSymbol):
    if sbSymbol not in oSelf.__doFunction_by_sbSymbol:
      oSelf.__doFunction_by_sbSymbol[sbSymbol] = cFunction(oSelf, sbSymbol);
    return oSelf.__doFunction_by_sbSymbol[sbSymbol];
  
  @property
  def bSymbolsAvailable(oSelf):
    if not oSelf.__bSymbolLoadingFailed and oSelf.__sbSymbolStatus in [b"deferred", b"export symbols", b"no symbols"]:
      # It's deferred or otherwise not loaded: try to load symbols now.
      asbLoadSymbolsOutput = oSelf.oProcess.fasbExecuteCdbCommand(
        sbCommand = b"ld %s;" % oSelf.sbCdbId,
        sb0Comment = b"Load symbols for module %s@0x%X" % (oSelf.sbCdbId, oSelf.uStartAddress),
        bRetryOnTruncatedOutput = True,
      );
      if asbLoadSymbolsOutput != [b"Symbol load for %s failed" % oSelf.sbCdbId]:
        assert len(asbLoadSymbolsOutput) == 1 and re.match(rb"Symbols (already )?loaded for %s" % oSelf.sbCdbId, asbLoadSymbolsOutput[0]), \
            "Unexpected load symbols output:\r\n%s" % \
            "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbLoadSymbolsOutput);
        # Unfortunately, it does not tell us if it loaded a pdb, or if export symbols are used.
        # So we will call __fzGetModuleSymbolAndVersionInformation again to find out.
        oSelf.__fzGetModuleSymbolAndVersionInformation();
        assert oSelf.__sbSymbolStatus != b"deferred", \
            "Symbols are still reported as deferred after attempting to load them";
      if oSelf.__sbSymbolStatus in [b"deferred", b"export symbols", b"no symbols"]:
        # Loading the symbols failed; force reload all modules and overwriting any cached pdbs.
        oSelf.oProcess.fasbExecuteCdbCommand(
          sbCommand = b"!sym noisy; .block {.reload /f /o /v /w %s;}; !sym quiet;" % oSelf.sb0BinaryName,
          sb0Comment = b"Reload symbols for module %s@0x%X" % (oSelf.sbCdbId, oSelf.uStartAddress),
          bRetryOnTruncatedOutput = True,
        );
        oSelf.__fzGetModuleSymbolAndVersionInformation();
        if oSelf.__sbSymbolStatus in [b"deferred", b"export symbols", b"no symbols"]:
          # We cannot load symbols for this module for some reason.
          oSelf.__bSymbolLoadingFailed = True;
        else:
          # We cannot reload the module if we do not know the binary name
          oSelf.__bSymbolLoadingFailed = True;
    return {
      b"export symbols": False,
      b"deferred": False,
      b"no symbols": False,
      b"pdb symbols": True,
      b"private pdb symbols": True,
    }[oSelf.__sbSymbolStatus];
  
  @property
  def s0BinaryPath(oSelf):
    if oSelf.__bBinaryPathSet:
      return oSelf.__s0BinaryPath;
    oSelf.__bBinaryPathSet = True; # At least, it will be below.
    
    oSelf.__s0BinaryPath = oSelf.oProcess.fs0GetBinaryPathForModuleAddress(oSelf.uStartAddress);
    if oSelf.__s0BinaryPath:
      return oSelf.__s0BinaryPath;
    
    asbDLLsOutput = oSelf.oProcess.fasbExecuteCdbCommand(
      sbCommand = b"!dlls -c 0x%X" % oSelf.uStartAddress,
      sb0Comment = b"Get binary information for module %s@0x%X" % (oSelf.sbCdbId, oSelf.uStartAddress),
      bRetryOnTruncatedOutput = True,
      bOutputIsInformative = True,
    );
    while asbDLLsOutput and asbDLLsOutput[0] in [b"", b"This is Win8 with the loader DAG."]:
      asbDLLsOutput.pop(0);
    if asbDLLsOutput and not grb_dlls_ErrorHeader.match(asbDLLsOutput[0]):
      obFirstLineMatch = grb_dlls_OutputLine.match(asbDLLsOutput[0]);
      assert obFirstLineMatch, \
          "Unrecognized !dlls output first line : %s\r\n%s" % \
            (repr(asbDLLsOutput[0]), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDLLsOutput));
      sb0BinaryPath = obFirstLineMatch.group(1);
      oSelf.__s0BinaryPath = str(sb0BinaryPath, "ascii", "replace");
      return oSelf.__s0BinaryPath;
    return None;
  
  @property
  def s0BinaryName(oSelf):
    s0BinaryPath = oSelf.s0BinaryPath;
    return os.path.basename(s0BinaryPath) if s0BinaryPath is not None else None;
  @property
  def sb0BinaryName(oSelf):
    s0BinaryName = oSelf.s0BinaryName;
    return bytes(s0BinaryName, "ascii", "replace") if s0BinaryName is not None else None;
  
  # The below are never available until __fzGetModuleSymbolAndVersionInformation is called:
  @property
  def sb0FileVersion(oSelf):
    if not oSelf.__bModuleSymbolAndVersionInformationAvailable:
      oSelf.__fzGetModuleSymbolAndVersionInformation();
    return oSelf.__sb0FileVersion;
  @property
  
  def sb0Timestamp(oSelf):
    if not oSelf.__bModuleSymbolAndVersionInformationAvailable:
      oSelf.__fzGetModuleSymbolAndVersionInformation();
    return oSelf.__sb0Timestamp;
  
  @property
  def sb0SimplifiedName(oSelf):
    sb0BinaryName = oSelf.sb0BinaryName;
    return sb0BinaryName.lower() if sb0BinaryName else None;
  
  @property
  def sb0UniqueName(oSelf):
    sb0BinaryName = oSelf.sb0BinaryName;
    return sb0BinaryName.lower() if sb0BinaryName else None;
  
  @property
  def sInformationHTML(oSelf):
    if not oSelf.__bModuleSymbolAndVersionInformationAvailable:
      oSelf.__fzGetModuleSymbolAndVersionInformation();
    s0BinaryName = oSelf.s0BinaryName;
    return "".join([
      "<h2 class=\"SubHeader\">%s</h2>" % (
        fsCP437HTMLFromString(s0BinaryName) if s0BinaryName
        else "<unknown binary>"
      ),
      "<table>",
    ] + [
      "<tr><td>%s</td><td>%s</td></tr>" % (fsCP437HTMLFromBytesString(sbName), fsCP437HTMLFromBytesString(sbValue))
          for (sbName, sbValue) in oSelf.__atsbModuleInformationNameAndValuePairs
    ] + [
      "</table>",
    ]);
  
  @staticmethod
  def fo0CreateForStartAddress(oProcess, uStartAddress):
    return cModule.__fo0GetOrCreateFrom_lmov(oProcess, b"a 0x%X;" % uStartAddress);
    
  @staticmethod
  def fo0CreateForCdbId(oProcess, sbCdbId):
    return cModule.__fo0GetOrCreateFrom_lmov(oProcess, b"m %s;" % sbCdbId);
  
  @staticmethod
  def __fo0GetOrCreateFrom_lmov(oProcess, sb_lmov_Arguments):
    asb_lmov_Output = oProcess.fasbExecuteCdbCommand(
      sbCommand = b"lmov %s" % sb_lmov_Arguments,
      sb0Comment = b"Get module information",
      bRetryOnTruncatedOutput = True,
      bOutputIsInformative = True,
    );
    assert len(asb_lmov_Output), \
        "Got no \"lmov %s\" output!" % (
          fsCP437FromBytesString(sb_lmov_Arguments),
        );
    assert grb_lm_Header.match(asb_lmov_Output[0]), \
        "Unrecognized \"lmov %s\" output first line:\r\n%s" % (
          fsCP437FromBytesString(sb_lmov_Arguments),
          "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asb_lmov_Output)
        );
    if len(asb_lmov_Output) == 1:
      return None; # There is no module here.
    assert len(asb_lmov_Output) > 2, \
        "Expected at least three lines of \"lmov %s\" output, got %d:\r\n%s" % (
          fsCP437FromBytesString(sb_lmov_Arguments),
          len(asb_lmov_Output),
          "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asb_lmov_Output)
        );
    (uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus) = ftxParse_lm_OutputAddresssesCdbIdAndSymbolStatus(asb_lmov_Output[1]);
    oModule = oProcess.foGetOrCreateModule(uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus);
    assert oModule.__fbProcess_lmov_Output(asb_lmov_Output), \
        "'lmov' output cannot be processed: %s" % repr(asb_lmov_Output);
    return oModule;
  
  @staticmethod
  def faoGetOrCreateAll(oProcess):
    asb_lmo_Output = oProcess.fasbExecuteCdbCommand(
      sbCommand = b"lmo;",
      sb0Comment = b"Get basic information on all loaded modules",
      bRetryOnTruncatedOutput = True,
      bOutputIsInformative = True,
    );
    assert len(asb_lmo_Output) > 1, \
        "Expected at least two lines of module information output, got %d:\r\n%s" % \
        (len(asb_lmo_Output), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asb_lmo_Output));
    assert grb_lm_Header.match(asb_lmo_Output[0]), \
        "Unrecognized list modules output header: %s\r\n%s" % \
        (repr(asb_lmo_Output[0]), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asb_lmo_Output));
    aoModules = [];
    for sbLine in asb_lmo_Output[1:]:
      (uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus) = ftxParse_lm_OutputAddresssesCdbIdAndSymbolStatus(sbLine);
      aoModules.append(oProcess.foGetOrCreateModule(uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus));
    return aoModules;
  
  def __fzGetModuleSymbolAndVersionInformation(oSelf):
    # Gather version information and optionally returns output for use in HTML report.
    # Also sets oSelf.sFileVersion if possible.
    assert (
      oSelf.__fbProcess_lmov_Output(oSelf.oProcess.fasbExecuteCdbCommand(
        sbCommand = b"lmov a 0x%X;" % oSelf.uStartAddress,
        sb0Comment = b"Get module information for module %s@0x%X using address" % (oSelf.sbCdbId, oSelf.uStartAddress),
        bRetryOnTruncatedOutput = True,
        bOutputIsInformative = True,
      )) or oSelf.__fbProcess_lmov_Output(oSelf.oProcess.fasbExecuteCdbCommand(
        sbCommand = b"lmov m %s;" % oSelf.sbCdbId,
        sb0Comment = b"Get module information for module %s@0x%X using name" % (oSelf.sbCdbId, oSelf.uStartAddress),
        bRetryOnTruncatedOutput = True,
        bOutputIsInformative = True,
      ))
    ), \
        "Cannot get module symbol and version information for module %s@0x%X!" % (oSelf.sbCdbId, oSelf.uStartAddress);
  
  def __fbProcess_lmov_Output(oSelf, asb_lmov_Output):
    # Sample output:
    # |0:004> lmov a 0x011b0000
    # |start             end                 module name
    # |00000000`011b0000 00000000`0120f000   firefox    (deferred)             
    # |    Image path: firefox.exe
    # |    Image name: firefox.exe
    # |    Image was built with /Brepro flag.
    # |    Timestamp:        Thu Aug 13 03:23:30 2015 (55CBF192)
    # |    CheckSum:         0006133B
    # |    ImageSize:        0005F000
    # |    File version:     40.0.2.5702
    # |    Product version:  40.0.2.0
    # |    File flags:       0 (Mask 3F)
    # |    File OS:          4 Unknown Win32
    # |    File type:        2.0 Dll
    # |    File date:        00000000.00000000
    # |    Translations:     0000.04b0
    # |    CompanyName:      Mozilla Corporation
    # |    ProductName:      Firefox
    # |    InternalName:     Firefox
    # |    OriginalFilename: firefox.exe
    # |    ProductVersion:   40.0.2
    # |    FileVersion:      40.0.2
    # |    FileDescription:  Firefox
    # |    LegalCopyright:   (c)Firefox and Mozilla Developers; available under the MPL 2 license.
    # |    LegalTrademarks:  Firefox is a Trademark of The Mozilla Foundation.
    # |    Comments:         Firefox is a Trademark of The Mozilla Foundation.
    # The first two lines can be skipped.
    oSelf.__atsbModuleInformationNameAndValuePairs = [];
    if len(asb_lmov_Output) == 1:
      return False;
    assert len(asb_lmov_Output) > 2, \
        "Expected at least 3 lines of list module output, got %d:\r\n%s" % \
        (len(asb_lmov_Output), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asb_lmov_Output));
    assert grb_lm_Header.match(asb_lmov_Output[0]), \
        "Unexpected list module output on line 1:\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asb_lmov_Output);
    (uStartAddress, uEndAddress, sbCdbId, sbSymbolStatus) = ftxParse_lm_OutputAddresssesCdbIdAndSymbolStatus(asb_lmov_Output[1]);
    assert oSelf.uStartAddress == uStartAddress, \
        "Module start address was given as 0x%X, but is now reported to be 0x%X" % (oSelf.uStartAddress, uStartAddress);
    assert oSelf.uEndAddress == uEndAddress, \
        "Module end address was given as 0x%X, but is now reported to be 0x%X" % (oSelf.uEndAddress, uEndAddress);
# After encountering many odd bugs, and many hours spent trying to find out what was going on, I found the cdb id for a module can change...
# Though the cdb developers may think this was a good idea, I tend to disagree. The code now tries to avoid using the cdb ids as much as possible.
#    assert oSelf.sbCdbId == sbCdbId, \
#        "Module cdb id was given as %s, but is now reported to be %s" % (repr(oSelf.sbCdbId), repr(sbCdbId));
    if oSelf.__sbSymbolStatus == b"deferred":
      # If the symbol status was deferred, we may have loaded the symbols, so this may have changed:
      oSelf.__sbSymbolStatus = sbSymbolStatus;
# I've seen the module symbol status go from "export symbols" to "deferred" for unknown reasons. Let's just ignore this.
#    else:
#      assert oSelf.__sbSymbolStatus == sbSymbolStatus, \
#        "Module symbol status was given as %s, but is now reported to be %s" % (repr(oSelf.__sbSymbolStatus), repr(sbSymbolStatus));
    
    dsbValue_by_sbName = {};
    for sbLine in asb_lmov_Output[2:]:
      # These lines different from the "name: value" format and handled separately:
      if sbLine.strip() in [
        b"Image was built with /Brepro flag.",
        b"Has CLR image header, track-debug-data flag not set",
        b"Information from resource tables:",
      ]:
        continue; # Ignored.
      oNameAndValueMatch = re.match(rb"^\s+([^:]+):\s+(.*?)\s*$", sbLine);
      assert oNameAndValueMatch, \
          "Unexpected list module output: %s\r\n%s" % \
          (sbLine, "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asb_lmov_Output));
      (sbName, sbValue) = oNameAndValueMatch.groups();
      dsbValue_by_sbName[sbName] = sbValue;
      oSelf.__atsbModuleInformationNameAndValuePairs.append((sbName, sbValue));
# We no longer trust cdb output for the module binary path
#    sb0ModuleBinaryPath = dsbValue_by_sbName[b"Image path"] if b"Image path" in dsbValue_by_sbName else None;
#    if oSelf.__sb0BinaryPath is None and sb0ModuleBinaryPath:
#      # If the "Image path" is absolute, os.path.join will simply use that, otherwise it will be relative to the base path
#      sProcessBinaryPath = oSelf.oProcess.oWindowsAPIProcess.sBinaryPath;
#      if sProcessBinaryPath:
#        sProcessBinaryBasePath = os.path.dirname(sProcessBinaryPath);
#        try:
#          sb0ModuleBinaryPath = os.path.join(bytes(sProcessBinaryBasePath, "ascii", "strict"), sb0ModuleBinaryPath);
#        except UnicodeEncodeError:
#          pass;
#      # The above is kinda hacky, so check that the file exists before assuming the value is correct:
#      if os.path.isfile(sb0ModuleBinaryPath):
#        oSelf.__sb0BinaryPath = sb0ModuleBinaryPath;
#    oSelf.__sb0BinaryName = os.path.basename(sb0ModuleBinaryPath).lower() if sb0ModuleBinaryPath else None;
    oSelf.__sb0FileVersion = dsbValue_by_sbName.get(b"File version");
    oSelf.__sb0Timestamp = dsbValue_by_sbName[b"Timestamp"];
    
    oSelf.__bModuleSymbolAndVersionInformationAvailable = True;
    return True;
