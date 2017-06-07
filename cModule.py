import os, re;
from cFunction import cFunction;

class cModule(object):
  def __init__(oModule, oProcess, uStartAddress, uEndAddress, sCdbId, sSymbolStatus):
    oModule.oProcess = oProcess;
    oModule.uStartAddress = uStartAddress;
    oModule.uEndAddress = uEndAddress;
    oModule.sCdbId = sCdbId;
    oModule.__sSymbolStatus = sSymbolStatus; # Not exposed; use bSymbolsAvailable
    # __fGetModuleInformation needs only be called once:
    oModule.__bModuleInformationAvailable = False; # set to false when __fGetModuleInformation is called.
    oModule.__sBinaryName = None;
    oModule.__sFileVersion = None;
    oModule.__sTimestamp = None;
    oModule.__sInformationHTML = None;
    oModule.__doFunction_by_sSymbol = {};
    oModule.sISA = oProcess.sISA; # x86/x64 processes are assumed to only load x86/x64 modules respectively.
  
  def foGetOrCreateFunctionForSymbol(oModule, sSymbol):
    if sSymbol not in oModule.__doFunction_by_sSymbol:
      oModule.__doFunction_by_sSymbol[sSymbol] = cFunction(oModule, sSymbol);
    return oModule.__doFunction_by_sSymbol[sSymbol];
  
  @property
  def bSymbolsAvailable(oModule):
    if oModule.__sSymbolStatus == "deferred":
      # It's deferred: try to load symbols now.
      asLoadSymbolsOutput = oModule.oProcess.fasExecuteCdbCommand("ld %s; $$ Load symbols for module" % oModule.sCdbId);
      assert len(asLoadSymbolsOutput) == 1 and re.match(r"Symbols (already )?loaded for %s" % oModule.sCdbId, asLoadSymbolsOutput[0]), \
          "Unexpected load symbols output:\r\n%s" % "\r\n".join(asLoadSymbolsOutput);
      # Unfortunately, it does not tell us if it loaded a pdb, or if export symbols are used.
      # So we will call __fGetModuleInformation again to find out.
      oModule.__fGetModuleInformation();
      assert oModule.__sSymbolStatus != "deferred", \
          "Symbol loading reported success, but symbols are still reported as deferred";
    return {
      "export symbols": False,
      "no symbols": False,
      "pdb symbols": True,
      "private pdb symbols": True,
    }[oModule.__sSymbolStatus];
  
  # The below are never available until __fGetModuleInformation is called:
  @property
  def sBinaryName(oModule):
    if not oModule.__bModuleInformationAvailable:
      oModule.__fGetModuleInformation();
    return oModule.__sBinaryName;
  
  @property
  def sFileVersion(oModule):
    if not oModule.__bModuleInformationAvailable:
      oModule.__fGetModuleInformation();
    return oModule.__sFileVersion;
  @property
  
  def sTimestamp(oModule):
    if not oModule.__bModuleInformationAvailable:
      oModule.__fGetModuleInformation();
    return oModule.__sTimestamp;
  
  @property
  def sSimplifiedName(oModule):
    return oModule.sBinaryName.lower();
  
  @property
  def sUniqueName(oModule):
    return oModule.sBinaryName.lower();
  
  @property
  def sInformationHTML(oModule):
    if not oModule.__bModuleInformationAvailable:
      oModule.__fGetModuleInformation();
    return oModule.__sInformationHTML;
  
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
  
  def __fGetModuleInformation(oModule):
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
      asModuleInformationTableRowsHTML = [];
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
    else:
      assert oModule.__sSymbolStatus == sSymbolStatus, \
        "Module symbol status was given as %s, but is now reported to be %s" % (repr(oModule.__sSymbolStatus), repr(sSymbolStatus));
    
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
          asModuleInformationTableRowsHTML.append(
            '<tr><td>%s</td><td>%s</td></tr>' % (oCdbWrapper.fsHTMLEncode(sName), oCdbWrapper.fsHTMLEncode(sValue)),
          );
    oModule.__sBinaryName = "Image path" in dsValue_by_sName and os.path.basename(dsValue_by_sName["Image path"]) or None;
    oModule.__sFileVersion = dsValue_by_sName.get("File version");
    oModule.__sTimestamp = dsValue_by_sName["Timestamp"];
    if oCdbWrapper.bGenerateReportHTML:
      oModule.__sInformationHTML = "".join([
        "<h2 class=\"SubHeader\">%s</h2>" % oCdbWrapper.fsHTMLEncode(oModule.__sBinaryName or "<unknown binary>"),
        "<table>",
      ] + asModuleInformationTableRowsHTML + [
        "</table>",
      ]);
