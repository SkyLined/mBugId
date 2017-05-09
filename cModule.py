import re;
from cFunction import cFunction;

class cModule(object):
  def __init__(oModule, oProcess, sCdbId, uStartAddress = None, uEndAddress = None):
    oModule.oProcess = oProcess;
    oModule.sCdbId = sCdbId;
    oModule.__uStartAddress = uStartAddress;
    oModule.__uEndAddress = uEndAddress;
    oModule.__sBinaryName = None;
    oModule.__bSymbolsAvailable = None;
    oModule.__bSymbolsStatusKnown = False;
    oModule.__sFileVersion = None;
    oModule.__sTimestamp = None;
    oModule.__sInformationHTML = None;
    oModule.__doFunction_by_sSymbol = {};
    # The start address will have none of the upper 32 bits set on x86 for obvious reasons, but it will always have
    # some bits set on x64 (citation needed).
    oModule.sISA = uStartAddress < 0x100000000 and "x86" or "x64";
  
  def foGetOrCreateFunctionForSymbol(oModule, sSymbol):
    if sSymbol not in oModule.__doFunction_by_sSymbol:
      oModule.__doFunction_by_sSymbol[sSymbol] = cFunction(oModule, sSymbol);
    return oModule.__doFunction_by_sSymbol[sSymbol];
  
  @property
  def uStartAddress(oModule):
    if oModule.__uStartAddress is None:
      oModule.__fGetAddressesAndSymbolsStatus();
    return oModule.__uStartAddress;
  
  @property
  def uEndAddress(oModule):
    oCdbWrapper = oModule.oProcess.oCdbWrapper;
    if oModule.__uEndAddress is None:
      oModule.__fGetAddressesAndSymbolsStatus();
    return oModule.__uEndAddress;
  
  @property
  def bSymbolsAvailable(oModule):
    oCdbWrapper = oModule.oProcess.oCdbWrapper;
    if not oModule.__bSymbolsStatusKnown:
      # Find out the symbols status
      oModule.__fGetAddressesAndSymbolsStatus();
    if oModule.__bSymbolsAvailable is None:
      # It's deferred: try to load symbols
      asLoadSymbolsOutput = oCdbWrapper.fasSendCommandAndReadOutput("ld %s; $$ Load symbols for module" % oModule.sCdbId);
      assert len(asLoadSymbolsOutput) == 1 and re.match(r"Symbols (already )?loaded for %s" % oModule.sCdbId, asLoadSymbolsOutput[0]), \
          "Unexpected load symbols output:\r\n%s" % "\r\n".join(asLoadSymbolsOutput);
      # Unfortunately, it does not tell us if it loadad a pdb, or if export symbols are used.
      oModule.__fGetAddressesAndSymbolsStatus();
    return oModule.__bSymbolsAvailable;
  
  def __fGetAddressesAndSymbolsStatus(oModule):
    oProcess = oModule.oProcess;
    oCdbWrapper = oProcess.oCdbWrapper;
    oProcess.fSelectInCdb();
    asListModuleOutput = oCdbWrapper.fasSendCommandAndReadOutput("lmo m %s; $$ List addresses for module" % oModule.sCdbId);
    assert len(asListModuleOutput) == 2, \
        "Expected 2 lines of output, got %d:\r\n%s" % (len(asListModuleOutput), "\r\n".join(asListModuleOutput));
    oModule.__fParseListModuleFirstLines(asListModuleOutput);
  
  def __fParseListModuleFirstLines(oModule, asListModuleOutput):
    assert re.match("^start\s+end\s+module name\s*$", asListModuleOutput[0]), \
        "Unexpected list module output on line 1:\r\n%s" % "\r\n".join(asListModuleOutput);
    oStartAndEndAddressMatch = re.match(
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
    assert oStartAndEndAddressMatch, \
        "Unexpected list module output on line 2:\r\n%s" % "\r\n".join(asListModuleOutput);
    (sStartAddress, sEndAddress, sCdbId, sSymbolStatus) = oStartAndEndAddressMatch.groups();
    oModule.__uStartAddress = long(sStartAddress.replace("`", ""), 16);
    oModule.__uEndAddress = long(sEndAddress.replace("`", ""), 16);
    oModule.__bSymbolsAvailable = {
      "deferred": None,
      "export symbols": False,
      "no symbols": False,
      "pdb symbols": True,
      "private pdb symbols": True,
    }[sSymbolStatus];
    oModule.__bSymbolsStatusKnown = True;
  
  @property
  def sBinaryName(oModule):
    if oModule.__sBinaryName is None:
      oModule.__fGetBinaryInformation();
    return oModule.__sBinaryName;
  
  @property
  def sFileVersion(oModule):
    if oModule.__sFileVersion is None:
      oModule.__fGetBinaryInformation();
    return oModule.__sFileVersion;
  @property
  
  def sTimestamp(oModule):
    if oModule.__sTimestamp is None:
      oModule.__fGetBinaryInformation();
    return oModule.__sTimestamp;
  
  @property
  def sSimplifiedName(oModule):
    return oModule.sBinaryName.lower();
  
  @property
  def sUniqueName(oModule):
    return oModule.sBinaryName.lower();
  
  @property
  def sInformationHTML(oModule):
    if oModule.__sInformationHTML is None:
      oModule.__fGetBinaryInformation();
    return oModule.__sInformationHTML;
  
  def __fGetBinaryInformation(oModule):
    # Gather version information and optionally returns output for use in HTML report.
    # Also sets oModule.sFileVersion if possible.
    oProcess = oModule.oProcess;
    oCdbWrapper = oProcess.oCdbWrapper;
    oProcess.fSelectInCdb();
    asListModuleOutput = oCdbWrapper.fasSendCommandAndReadOutput(
      "lmv m *%s; $$ Get module information" % oModule.sCdbId,
      bOutputIsInformative = True,
    );
    # Sample output:
    # |0:004> lmv m firefox
    # |start             end                 module name
    # |00000000`011b0000 00000000`0120f000   firefox    (deferred)             
    # |    Image path: firefox.exe
    # |    Image name: firefox.exe
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
    oModule.__fParseListModuleFirstLines(asListModuleOutput);
    dsValue_by_sName = {};
    for sLine in asListModuleOutput[2:]:
      oNameAndValueMatch = re.match(r"^\s+([^:]+):\s+(.*?)\s*$", sLine);
      assert oNameAndValueMatch, \
          "Unexpected list module output: %s\r\n%s" % (sLine, "\r\n".join(asListModuleOutput));
      (sName, sValue) = oNameAndValueMatch.groups();
      dsValue_by_sName[sName] = sValue;
      if oCdbWrapper.bGenerateReportHTML:
        asModuleInformationTableRowsHTML.append(
          '<tr><td>%s</td><td>%s</td></tr>' % (oCdbWrapper.fsHTMLEncode(sName), oCdbWrapper.fsHTMLEncode(sValue)),
        );
    oModule.__sBinaryName = dsValue_by_sName.get("OriginalFilename") or dsValue_by_sName["Image name"];
    oModule.__sFileVersion = dsValue_by_sName.get("File version");
    oModule.__sTimestamp = dsValue_by_sName["Timestamp"];
    if oCdbWrapper.bGenerateReportHTML:
      oModule.__sInformationHTML = "".join([
        "<h2 class=\"SubHeader\">%s</h2>" % oCdbWrapper.fsHTMLEncode(oModule.__sBinaryName),
        "<table>",
      ] + asModuleInformationTableRowsHTML + [
        "</table>",
      ]);
