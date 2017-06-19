import os, re;
from cFunction import cFunction;

class cModule(object):
  def __init__(oModule, oProcess, uStartAddress, uEndAddress, sCdbId, sSymbolStatus):
    oModule.oProcess = oProcess;
    oModule.uStartAddress = uStartAddress;
    oModule.uEndAddress = uEndAddress;
    oModule.sCdbId = sCdbId;
    oModule.__sSymbolStatus = sSymbolStatus; # Not exposed; use bSymbolsAvailable
    # __fGetModuleSymbolAndVersionInformation needs only be called once:
    oModule.__bModuleSymbolAndVersionInformationAvailable = False; # set to false when __fGetModuleSymbolAndVersionInformation is called.
    oModule.__sBinaryPath = None;
    oModule.__sBinaryName = None;
    oModule.__sFileVersion = None;
    oModule.__sTimestamp = None;
    oModule.__doFunction_by_sSymbol = {};
    oModule.__atsModuleInformationNameAndValuePairs = None;
    oModule.sISA = oProcess.sISA; # x86/x64 processes are assumed to only load x86/x64 modules respectively.
  
  def foGetOrCreateFunctionForSymbol(oModule, sSymbol):
    if sSymbol not in oModule.__doFunction_by_sSymbol:
      oModule.__doFunction_by_sSymbol[sSymbol] = cFunction(oModule, sSymbol);
    return oModule.__doFunction_by_sSymbol[sSymbol];
  
  @property
  def bSymbolsAvailable(oModule):
    if oModule.__sSymbolStatus in ["deferred", "export symbols", "no symbols"]:
      # It's deferred or otherwise not loaded: try to load symbols now.
      asLoadSymbolsOutput = oModule.oProcess.fasExecuteCdbCommand("ld %s; $$ Load symbols for module" % oModule.sCdbId);
      assert len(asLoadSymbolsOutput) == 1 and re.match(r"Symbols (already )?loaded for %s" % oModule.sCdbId, asLoadSymbolsOutput[0]), \
          "Unexpected load symbols output:\r\n%s" % "\r\n".join(asLoadSymbolsOutput);
      # Unfortunately, it does not tell us if it loaded a pdb, or if export symbols are used.
      # So we will call __fGetModuleSymbolAndVersionInformation again to find out.
      oModule.__fGetModuleSymbolAndVersionInformation();
      assert oModule.__sSymbolStatus != "deferred", \
          "Symbol loading reported success, but symbols are still reported as deferred";
    return {
      "export symbols": False,
      "no symbols": False,
      "pdb symbols": True,
      "private pdb symbols": True,
    }[oModule.__sSymbolStatus];
  
  @property
  def sBinaryPath(oModule):
    if oModule.__sBinaryPath is None:
      asDLLsOutput = oModule.oProcess.fasExecuteCdbCommand(
        "!dlls -c 0x%X" % oModule.uStartAddress,
        bOutputIsInformative = True,
      );
      if asDLLsOutput:
        while asDLLsOutput[0] in ["", "This is Win8 with the loader DAG."]:
          asDLLsOutput.pop(0);
        oFirstLineMatch = re.match(r"^0x[0-9`a-f]+: ([A-Z]:\\.+)$", asDLLsOutput[0], re.I);
        assert oFirstLineMatch, \
            "Unrecognized !dlls output first line : %s\r\n%s" % (repr(asDLLsOutput[0]), "\r\n".join(asDLLsOutput));
        oModule.__sBinaryPath = oFirstLineMatch.group(1);
      else:
        # Of course, !dlls will sometimes not output anything for unknown reasons.
        # In this case we have to resort to less reliable measures.
        oModule.__fGetModuleSymbolAndVersionInformation();
    return oModule.__sBinaryPath;
  
  @property
  def sBinaryName(oModule):
    if oModule.__sBinaryPath is None:
      # "!dlls" may not work yet if the process was recently started, but "__fGetModuleSymbolAndVersionInformation"
      # uses "lm", which should give us eht name of the binary as well:
      if oModule.__sBinaryName is None:
        oModule.__fGetModuleSymbolAndVersionInformation();
      return oModule.__sBinaryName;
    return os.path.basename(oModule.sBinaryPath);
  
  # The below are never available until __fGetModuleSymbolAndVersionInformation is called:
  @property
  def sFileVersion(oModule):
    if not oModule.__bModuleSymbolAndVersionInformationAvailable:
      oModule.__fGetModuleSymbolAndVersionInformation();
    return oModule.__sFileVersion;
  @property
  
  def sTimestamp(oModule):
    if not oModule.__bModuleSymbolAndVersionInformationAvailable:
      oModule.__fGetModuleSymbolAndVersionInformation();
    return oModule.__sTimestamp;
  
  @property
  def sSimplifiedName(oModule):
    return oModule.sBinaryName.lower();
  
  @property
  def sUniqueName(oModule):
    return oModule.sBinaryName.lower();
  
  @property
  def sInformationHTML(oModule):
    if not oModule.__bModuleSymbolAndVersionInformationAvailable:
      oModule.__fGetModuleSymbolAndVersionInformation();
    fsHTMLEncode = oModule.oProcess.oCdbWrapper.fsHTMLEncode;
    return "".join([
      "<h2 class=\"SubHeader\">%s</h2>" % fsHTMLEncode(oModule.sBinaryName or "<unknown binary>"),
      "<table>",
    ] + [
      "<tr><td>%s</td><td>%s</td></tr>" % (fsHTMLEncode(sName), fsHTMLEncode(sValue))
      for sName, sValue in oModule.__atsModuleInformationNameAndValuePairs
    ] + [
      "</table>",
    ]);
  
  @staticmethod
  def ftxParseListModulesOutputLine(sListModulesOutputLine):
    oInformationMatch = re.match(
      r"^\s*%s\s*$" % "\s+".join([
        r"([0-9a-f`]+)",                              # (start_address)
        r"([0-9a-f`]+)",                              # (end_address)
        r"(\w+)(?:\s+C)?",                            # (cdb_module_id) [ space "C" ] # not sure what this "C" means
        r"\((deferred|(?:export|no|(?:private )?pdb) symbols)\)", # "(" symbol status ")"
        r".*?",                                       # symbol information.
      ]),
      sListModulesOutputLine,
      re.I
    );
    assert oInformationMatch, \
        "Unrecognized module basic information output: %s" % sListModulesOutputLine;
    (sStartAddress, sEndAddress, sCdbId, sSymbolStatus) = oInformationMatch.groups();
    uStartAddress = long(sStartAddress.replace("`", ""), 16);
    uEndAddress = long(sEndAddress.replace("`", ""), 16);
    return (uStartAddress, uEndAddress, sCdbId, sSymbolStatus);
  
  def __fGetModuleSymbolAndVersionInformation(oModule):
    # TODO: The HTML report output should really not be produced here (aka push the data). Rather, it should be created
    # on demand using another function call when the report is created (aka pull the data). This would also do away
    # with all references to oCdbWrapper
    
    # Gather version information and optionally returns output for use in HTML report.
    # Also sets oModule.sFileVersion if possible.
    oCdbWrapper = oModule.oProcess.oCdbWrapper;
    asListModuleOutput = oModule.oProcess.fasExecuteCdbCommand(
      "lmov a 0x%X; $$ Get module information" % oModule.uStartAddress,
      bOutputIsInformative = True,
    );
    # Sample output:
    # |0:004> lmv m firefox
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
    if oCdbWrapper.bGenerateReportHTML:
      oModule.__atsModuleInformationNameAndValuePairs = [];
    assert len(asListModuleOutput) > 2, \
        "Expected at least 3 lines of list module output, got %d:\r\n%s" % (len(asListModuleOutput), "\r\n".join(asListModuleOutput));
    assert re.match("^start\s+end\s+module name\s*$", asListModuleOutput[0]), \
        "Unexpected list module output on line 1:\r\n%s" % "\r\n".join(asListModuleOutput);
    (uStartAddress, uEndAddress, sCdbId, sSymbolStatus) = cModule.ftxParseListModulesOutputLine(asListModuleOutput[1]);
    assert oModule.uStartAddress == uStartAddress, \
        "Module start address was given as 0x%X, but is now reported to be 0x%X" % (oModule.uStartAddress, uStartAddress);
    assert oModule.uEndAddress == uEndAddress, \
        "Module end address was given as 0x%X, but is now reported to be 0x%X" % (oModule.uEndAddress, uEndAddress);
# After encountering many odd bugs, and many hours spent trying to find out what was going on, I found the cdb id for a module can change...
# Though the cdb developers may think this was a good idea, I tend to disagree. The code now tries to avoid using the cdb ids as much as possible.
#    assert oModule.sCdbId == sCdbId, \
#        "Module cdb id was given as %s, but is now reported to be %s" % (repr(oModule.sCdbId), repr(sCdbId));
    if oModule.__sSymbolStatus == "deferred":
      # If the symbol status was deferred, we may have loaded the symbols, so this may have changed:
      oModule.__sSymbolStatus = sSymbolStatus;
# I've seen the module symbol status go from "export symbols" to "deferred" for unknown reasons. Let's just ignore this.
#    else:
#      assert oModule.__sSymbolStatus == sSymbolStatus, \
#        "Module symbol status was given as %s, but is now reported to be %s" % (repr(oModule.__sSymbolStatus), repr(sSymbolStatus));
    
    dsValue_by_sName = {};
    for sLine in asListModuleOutput[2:]:
      # These lines different from the "name: value" format and handled separately:
      if sLine == "    Image was built with /Brepro flag.":
        continue; # Ignored.
      else:
        oNameAndValueMatch = re.match(r"^\s+([^:]+):\s+(.*?)\s*$", sLine);
        assert oNameAndValueMatch, \
            "Unexpected list module output: %s\r\n%s" % (sLine, "\r\n".join(asListModuleOutput));
        (sName, sValue) = oNameAndValueMatch.groups();
        dsValue_by_sName[sName] = sValue;
        if oCdbWrapper.bGenerateReportHTML:
          oModule.__atsModuleInformationNameAndValuePairs.append((sName, sValue));
    if oModule.__sBinaryPath is None and "Image path" in dsValue_by_sName:
      # If the "Image path" is absolute, os.path.join will simply use that, otherwise it will be relative to the base path
      if oModule.oProcess.sBasePath:
        sBinaryPath = os.path.join(oModule.oProcess.sBasePath, dsValue_by_sName["Image path"]);
      else:
        sBinaryPath = os.path.abspath(dsValue_by_sName["Image path"]);
      # The above is kinda hacky, so check that the file exists before assuming the value is correct:
      if os.path.isfile(sBinaryPath):
        oModule.__sBinaryPath = sBinaryPath;
    oModule.__sBinaryName = "Image path" in dsValue_by_sName and os.path.basename(dsValue_by_sName["Image path"]) or None;
    oModule.__sFileVersion = dsValue_by_sName.get("File version");
    oModule.__sTimestamp = dsValue_by_sName["Timestamp"];
    
    oModule.__bModuleSymbolAndVersionInformationAvailable = True;
