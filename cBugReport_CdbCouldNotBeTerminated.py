import mProductDetails;

from .dxConfig import dxConfig;
from .ftsReportLicenseHeaderAndFooterHTML import ftsReportLicenseHeaderAndFooterHTML;
from .ftsReportProductHeaderAndFooterHTML import ftsReportProductHeaderAndFooterHTML;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .sReportHTMLTemplate import sReportHTMLTemplate;

class cBugReport_CdbCouldNotBeTerminated(object):
  def __init__(oBugReport, oCdbWrapper):
    import cBugId;
    o0ProductDetails = (
      mProductDetails.fo0GetProductDetailsForMainModule()
      or mProductDetails.fo0GetProductDetailsForModule(mBugId)
    );
    oBugReport.s0BugTypeId = "CdbNotTerminated";
    oBugReport.s0BugDescription = "Cdb could not be terminated";
    oBugReport.sBugLocation = None;
    oBugReport.s0SecurityImpact = None;
    oBugReport.o0Stack = None;
    
    asBlocksHTML = [];
    
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application run log",
        "sCollapsed": "Collapsible", # ...but not Collapsed
        "sContent": oCdbWrapper.sLogHTML,
      });
    oBugReport.sProcessBinaryName = "cdb.exe";
    
    oBugReport.sId = oBugReport.s0BugTypeId; # Isn't None
    oBugReport.s0StackId = None;
    oBugReport.s0UniqueStackId = None;
    oBugReport.sBugSourceLocation = None;
    oBugReport.asVersionInformation = \
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
      oBugReport.sReportHTML = sReportHTMLTemplate % {
        "sId": oCdbWrapper.fsHTMLEncode(oBugReport.sId),
        "sOptionalUniqueStackId": "",
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation or "Unknown"),
        "sOptionalSource": "",
        "sBugDescription": oCdbWrapper.fsHTMLEncode(oBugReport.s0BugDescription), # Isn't None
        "sBinaryVersion": "Not available",
        "sSecurityImpact": (
            "None" if oBugReport.s0SecurityImpact is None
            else ('<span class="SecurityImpact">%s</span>' % oCdbWrapper.fsHTMLEncode(oBugReport.s0SecurityImpact))
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
      oBugReport.sReportHTML = None;
  
  def fReport(oBugReport, oCdbWrapper):
    assert oCdbWrapper.fbFireCallbacks("Bug report", oBugReport), \
        "You really should add an event handler for \"Bug report\" events, as reporting bugs is cBugIds purpose";
