import mProductDetails;

from .cErrorDetails import cErrorDetails;
from .dxConfig import dxConfig;
from .ftsReportLicenseHeaderAndFooterHTML import ftsReportLicenseHeaderAndFooterHTML;
from .ftsReportProductHeaderAndFooterHTML import ftsReportProductHeaderAndFooterHTML;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .sReportHTMLTemplate import sReportHTMLTemplate;

class cBugReport_CdbTerminatedUnexpectedly(object):
  bIsInternalBug = True;
  def __init__(oBugReport, oCdbWrapper, uExitCode):
    import mBugId;
    o0ProductDetails = (
      mProductDetails.fo0GetProductDetailsForMainModule()
      or mProductDetails.fo0GetProductDetailsForModule(mBugId)
    );
    if uExitCode < 0:
      uExitCode += 1 << 32;
    uWindowsStatusOrErrorCode = uExitCode & 0xCFFFFFFF;
    o0ErrorDetails = cErrorDetails.fo0GetForCode(uWindowsStatusOrErrorCode);
    if o0ErrorDetails:
      oBugReport.s0BugTypeId = "CdbTerminated:%s" % (o0ErrorDetails.sTypeId or o0ErrorDetails.sDefineName);
      oBugReport.s0BugDescription = "Cdb terminated unexpectedly with exit code %s" % o0ErrorDetails.sDescription;
      oBugReport.s0SecurityImpact = o0ErrorDetails.s0SecurityImpact;
    else:
      oBugReport.s0BugTypeId = "CdbTerminated:0x%X" % uExitCode;
      oBugReport.s0BugDescription = "Cdb terminated unexpectedly with exit code 0x%X." % uExitCode;
      oBugReport.s0SecurityImpact = None;
    oBugReport.sBugLocation = "cdb.exe!(unknown)";
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
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation),
        "sOptionalSource": "",
        "sBugDescription": oCdbWrapper.fsHTMLEncode(oBugReport.s0BugDescription), # Isn't None
        "sBinaryVersion": "Not available",
        "sSecurityImpact": (
          "None" if oBugReport.s0SecurityImpact is None else
          '<span class="SecurityImpact">%s</span>' % oCdbWrapper.fsHTMLEncode(oBugReport.s0SecurityImpact)
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
