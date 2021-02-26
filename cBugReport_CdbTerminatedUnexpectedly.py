import cBugId, mProductDetails;

from .cErrorDetails import cErrorDetails;
from .dxConfig import dxConfig;
from .ftsReportLicenseHeaderAndFooterHTML import ftsReportLicenseHeaderAndFooterHTML;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .sReportHTMLTemplate import sReportHTMLTemplate;

class cBugReport_CdbTerminatedUnexpectedly(object):
  def __init__(oBugReport, oCdbWrapper, uExitCode):
    oProductDetails = (
      mProductDetails.foGetProductDetailsForMainModule()
      or mProductDetails.foGetProductDetailsForModule(cBugId)
    );
    if uExitCode < 0:
      uExitCode += 1 << 32;
    uWindowsStatusOrErrorCode = uExitCode & 0xCFFFFFFF;
    o0ErrorDetails = cErrorDetails.fo0GetForCode(uWindowsStatusOrErrorCode);
    if o0ErrorDetails:
      oBugReport.sBugTypeId = "CdbTerminated:%s" % (o0ErrorDetails.s0TypeId or o0ErrorDetails.sDefineName);
      oBugReport.sBugDescription = "Cdb terminated unexpectedly with exit code %s" % o0ErrorDetails.sDescription;
      oBugReport.sSecurityImpact = o0ErrorDetails.s0SecurityImpact;
    else:
      oBugReport.sBugTypeId = "CdbTerminated:0x%X" % uExitCode;
      oBugReport.sBugDescription = "Cdb terminated unexpectedly with exit code 0x%X." % uExitCode;
      oBugReport.sSecurityImpact = None;
    oBugReport.sBugLocation = "cdb.exe!(unknown)";
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
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation),
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
