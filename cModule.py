import os, re;
from cFunction import cFunction;

class cModule(object):
  def __init__(oModule, oProcess, sCdbId = None, uStartAddress = None, uEndAddress = None):
    oModule.oProcess = oProcess;
    # oModule.sCdbId is not always known from the start and may only be determined when needed using __fGetModuleInformation.
    oModule.__sCdbId = sCdbId;
    # oModule.uStartAddress is not always known from the start and may only be determined when needed using __fGetModuleInformation.
    oModule.__uStartAddress = uStartAddress;
    # oModule.uEndAddress is not always known from the start and may only be determined when needed using __fGetModuleInformation.
    oModule.__uEndAddress = uEndAddress;
    # oModule.bSymbolsAvailable is only determined when needed using __fGetModuleInformation
    oModule.__bSymbolsAvailable = None;
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
  
  # The below three may have been provided in the constructors arguments, so we may not need to call __fGetModuleInformation.
  @property
  def sCdbId(oModule):
    if oModule.__sCdbId is None:
      oModule.__fGetModuleInformation();
    return oModule.__sCdbId;
  
  @property
  def uStartAddress(oModule):
    if oModule.__uStartAddress is None:
      oModule.__fGetModuleInformation();
    return oModule.__uStartAddress;
  
  @property
  def uEndAddress(oModule):
    if oModule.__uEndAddress is None:
      oModule.__fGetModuleInformation();
    return oModule.__uEndAddress;
  
  # The below are never available until __fGetModuleInformation is called:
  @property
  def bSymbolsAvailable(oModule):
    if not oModule.__bModuleInformationAvailable:
      oModule.__fGetModuleInformation();
    # Find out the symbols status
    if oModule.__bSymbolsAvailable is None:
      # It's deferred: try to load symbols
      asLoadSymbolsOutput = oModule.oProcess.fasExecuteCdbCommand("ld %s; $$ Load symbols for module" % oModule.sCdbId);
      assert len(asLoadSymbolsOutput) == 1 and re.match(r"Symbols (already )?loaded for %s" % oModule.sCdbId, asLoadSymbolsOutput[0]), \
          "Unexpected load symbols output:\r\n%s" % "\r\n".join(asLoadSymbolsOutput);
      # Unfortunately, it does not tell us if it loaded a pdb, or if export symbols are used.
      # So we will call __fGetModuleInformation again to find out.
      oModule.__fGetModuleInformation();
    return oModule.__bSymbolsAvailable;
  
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
  
  def __fGetModuleInformation(oModule):
    # TODO: The HTML report output should really not be produced here (aka push the data). Rather, it should be created
    # on demand using another function call when the report is created (aka pull the data). This would also do away
    # with all references to oCdbWrapper
    
    # Gather version information and optionally returns output for use in HTML report.
    # Also sets oModule.sFileVersion if possible.
    oCdbWrapper = oModule.oProcess.oCdbWrapper;
    asListModuleOutput = oModule.oProcess.fasExecuteCdbCommand(
        oModule.__sCdbId and "lmov m %s; $$ Get module information" % oModule.__sCdbId
        or "lmov a 0x%X; $$ Get module information" % oModule.uStartAddress,
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
    oAddressesAndSymbolStatusMatch = re.match(
      r"^\s*%s\s*$" % "\s+".join([
        r"([0-9a-f`]+)",                              # (start_address)
        r"([0-9a-f`]+)",                              # (end_address)
        r"(\w+)(?:\s+C)?",                            # (cdb_module_id) [ space "C" ] # not sure what this "C" means
        r"\((deferred|(?:export|no|(?:private )?pdb) symbols)\)", # "(" symbol status ")"
        r".*?",                                       # symbol information.
      ]),
      asListModuleOutput[1],
      re.I
    );
    assert oAddressesAndSymbolStatusMatch, \
        "Unexpected list module output on line 2:\r\n%s" % "\r\n".join(asListModuleOutput);
    (sStartAddress, sEndAddress, sCdbId, sSymbolStatus) = oAddressesAndSymbolStatusMatch.groups();
    uStartAddress = long(sStartAddress.replace("`", ""), 16);
    uEndAddress = long(sEndAddress.replace("`", ""), 16);
    assert oModule.__uStartAddress in [None, uStartAddress], \
        "Module start address was given as 0x%X, but is now reported to be 0x%X" % (oModule.__uStartAddress, uStartAddress);
    assert oModule.__uEndAddress in [None, uEndAddress], \
        "Module end address was given as 0x%X, but is now reported to be 0x%X" % (oModule.__uEndAddress, uEndAddress);
    assert oModule.__sCdbId in [None, sCdbId], \
        "Module cdb id was given as %s, but is now reported to be %s" % (repr(oModule.__sCdbId), repr(sCdbId));
    oModule.__uStartAddress = uStartAddress;
    oModule.__uEndAddress = uEndAddress;
    oModule.__sCdbId = sCdbId;
    oModule.__bSymbolsAvailable = {
      "deferred": None,
      "export symbols": False,
      "no symbols": False,
      "pdb symbols": True,
      "private pdb symbols": True,
    }[sSymbolStatus];
    
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
