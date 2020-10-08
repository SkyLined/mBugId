from .dxConfig import dxConfig;
from ftsReportLicenseHeaderAndFooterHTML import ftsReportLicenseHeaderAndFooterHTML;
import mProductDetails;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .sReportHTMLTemplate import sReportHTMLTemplate;

import cBugId;

class cBugReport_CdbCouldNotBeTerminated(object):
  def __init__(oBugReport, oCdbWrapper):
    oProductDetails = (
      mProductDetails.foGetProductDetailsForMainModule()
      or mProductDetails.foGetProductDetailsForModule(cBugId)
    );
    oBugReport.sBugTypeId = "CdbNotTerminated";
    oBugReport.sBugDescription = "Cdb could not be terminated";
    oBugReport.sBugLocation = None;
    oBugReport.sSecurityImpact = None;
    oBugReport.oException = None;
    oBugReport.oStack = None;
    
    asBlocksHTML = [];
    
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application run log",
        "sCollapsed": "Collapsible", # ...but not Collapsed
        "sContent": oCdbWrapper.sLogHTML,
      });
    oBugReport.sProcessBinaryName = "cdb.exe";
    
    oBugReport.sId = oBugReport.sBugTypeId;
    oBugReport.sStackId = None;
    oBugReport.sBugSourceLocation = None;
    oBugReport.asVersionInformation = ["%s: %s" % (oProductDetails.sProductName, oProductDetails.oProductVersion)];
    if oCdbWrapper.bGenerateReportHTML:
      # Add Cdb IO to HTML report
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application and cdb output log",
        "sCollapsed": "Collapsed",
        "sContent": oCdbWrapper.sCdbIOHTML
      });
      # Create HTML details
      (sLicenseHeaderHTML, sLicenseFooterHTML) = ftsReportLicenseHeaderAndFooterHTML(oProductDetails);
      oBugReport.sReportHTML = sReportHTMLTemplate % {
        "sId": oCdbWrapper.fsHTMLEncode(oBugReport.sId),
        "sOptionalUniqueStackId": "",
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation or "Unknown"),
        "sOptionalSource": "",
        "sBugDescription": oCdbWrapper.fsHTMLEncode(oBugReport.sBugDescription),
        "sBinaryVersion": "Not available",
        "sSecurityImpact": oBugReport.sSecurityImpact and \
              '<span class="SecurityImpact">%s</span>' % oCdbWrapper.fsHTMLEncode(oBugReport.sSecurityImpact) or "None",
        "sOptionalIntegrityLevel": "",
        "sOptionalMemoryUsage": "",
        "sOptionalApplicationArguments": "",
        "sBlocks": "\r\n".join(asBlocksHTML),
        "sCdbStdIO": oCdbWrapper.sCdbIOHTML,
        "sProductName": oProductDetails.sProductName,
        "sProductVersion": oProductDetails.oProductVersion,
        "sProductAuthor": oProductDetails.sProductAuthor,
        "sProductURL": oProductDetails.sProductURL,
        "sLicenseHeader": sLicenseHeaderHTML,
        "sLicenseFooter": sLicenseFooterHTML,
      };
    else:
      oBugReport.sReportHTML = None;
  
  def fReport(oBugReport, oCdbWrapper):
    assert oCdbWrapper.fbFireCallbacks("Bug report", oBugReport), \
        "You really should add an event handler for \"Bug report\" events, as reporting bugs is cBugIds purpose";
