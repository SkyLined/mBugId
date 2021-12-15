import mProductDetails;

from .dxConfig import dxConfig;
from .ftsReportLicenseHeaderAndFooterHTML import ftsReportLicenseHeaderAndFooterHTML;
from .ftsReportProductHeaderAndFooterHTML import ftsReportProductHeaderAndFooterHTML;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .sReportHTMLTemplate import sReportHTMLTemplate;

class cBugReport_UnhandledPythonException(object):
  bIsInternalBug = True;
  def __init__(oSelf, oCdbWrapper, oException):
    import mBugId;
    o0ProductDetails = (
      mProductDetails.fo0GetProductDetailsForMainModule()
      or mProductDetails.fo0GetProductDetailsForModule(mBugId)
    );
    oSelf.s0BugTypeId = repr(oException);
    oSelf.s0BugDescription = repr(oException);
    oSelf.sBugLocation = None;
    oSelf.s0SecurityImpact = None;
    oSelf.o0Stack = None;
    
    asBlocksHTML = [];
    
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application run log",
        "sCollapsed": "Collapsible", # ...but not Collapsed
        "sContent": oCdbWrapper.sLogHTML,
      });
    oSelf.sProcessBinaryName = "python.exe";
    
    oSelf.sId = oSelf.s0BugTypeId; # Isn't None
    oSelf.s0StackId = None;
    oSelf.s0UniqueStackId = None;
    oSelf.sBugSourceLocation = None;
    oSelf.asVersionInformation = \
        ["%s: %s" % (o0ProductDetails.sProductName, o0ProductDetails.oProductVersion)] if o0ProductDetails else [];
    if oCdbWrapper.bGenerateReportHTML:
      # Add Cdb IO to HTML report
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application and cdb output log",
        "sCollapsed": "Collapsed",
        "sContent": oCdbWrapper.sCdbIOHTML
      });
      # Create HTML details
      if o0ProductDetails:
        (sProductHeaderHTML, sProductFooterHTML) = ftsReportProductHeaderAndFooterHTML(o0ProductDetails);
        (sLicenseHeaderHTML, sLicenseFooterHTML) = ftsReportLicenseHeaderAndFooterHTML(o0ProductDetails);
      else:
        sProductHeaderHTML = sProductFooter = sLicenseHeaderHTML = sLicenseFooterHTML = "";
      oSelf.sReportHTML = sReportHTMLTemplate % {
        "sId": oCdbWrapper.fsHTMLEncode(oSelf.sId),
        "sOptionalUniqueStackId": "",
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oSelf.sBugLocation or "Unknown"),
        "sOptionalSource": "",
        "sBugDescription": oCdbWrapper.fsHTMLEncode(oSelf.s0BugDescription), # Isn't None
        "sBinaryVersion": "Not available",
        "sSecurityImpact": (
            "None" if oSelf.s0SecurityImpact is None
            else ('<span class="SecurityImpact">%s</span>' % oCdbWrapper.fsHTMLEncode(oSelf.s0SecurityImpact))
        ),
        "sOptionalIntegrityLevel": "",
        "sOptionalMemoryUsage": "",
        "sOptionalApplicationArguments": "",
        "sBlocks": "\r\n".join(asBlocksHTML),
        "sCdbStdIO": oCdbWrapper.sCdbIOHTML,
        "sProductHeader": sProductHeaderHTML,
        "sProductFooter": sProductFooterHTML,
        "sLicenseHeader": sLicenseHeaderHTML,
        "sLicenseFooter": sLicenseFooterHTML,
      };
    else:
      oSelf.sReportHTML = None;
  
  def fReport(oSelf, oCdbWrapper):
    assert oCdbWrapper.fbFireCallbacks("Bug report", oSelf), \
        "You really should add an event handler for \"Bug report\" events, as reporting bugs is cBugIds purpose";
