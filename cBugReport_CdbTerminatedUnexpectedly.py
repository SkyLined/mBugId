from sBlockHTMLTemplate import sBlockHTMLTemplate;
from sReportHTMLTemplate import sReportHTMLTemplate;
from oVersionInformation import oVersionInformation;

class cBugReport_CdbTerminatedUnexpectedly(object):
  def __init__(oBugReport, oCdbWrapper, uExitCode):
    if uExitCode < 0:
      uExitCode += 1 << 32;
    oBugReport.sBugTypeId = "CdbTerminated:0x%X" % uExitCode;
    oBugReport.sBugDescription = "Cdb terminated unexpectedly";
    oBugReport.sBugLocation = None;
    oBugReport.sSecurityImpact = None;
    oBugReport.oException = None;
    oBugReport.oStack = None;
    
    if oCdbWrapper.bGenerateReportHTML:
      oBugReport.sImportantOutputHTML = oCdbWrapper.sImportantOutputHTML;
    oBugReport.sProcessBinaryName = "cdb.exe";
    
    oBugReport.sId = oBugReport.sBugTypeId;
    oBugReport.sStackId = None;
    oBugReport.sBugSourceLocation = None;
    oBugReport.asVersionInformation = ["cBugId: %s" % oVersionInformation.sCurrentVersion];
    
    if oCdbWrapper.bGenerateReportHTML:
      # Create HTML details
      oBugReport.sReportHTML = sReportHTMLTemplate % {
        "sId": oCdbWrapper.fsHTMLEncode(oBugReport.sId),
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation or "Unknown"),
        "sOptionalSource": "",
        "sBugDescription": oCdbWrapper.fsHTMLEncode(oBugReport.sBugDescription),
        "sBinaryVersion": "Not available",
        "sSecurityImpact": oBugReport.sSecurityImpact and \
              '<span class="SecurityImpact">%s</span>' % oCdbWrapper.fsHTMLEncode(oBugReport.sSecurityImpact) or "None",
        "sOptionalIntegrityLevel": "",
        "sOptionalApplicationArguments": "",
        "sBugIdVersion": oVersionInformation.sCurrentVersion,
        "sBlocks": sBlockHTMLTemplate % {
          "sName": "Application and cdb output log",
          "sCollapsed": "Collapsed",
          "sContent": oCdbWrapper.sCdbIOHTML
        },
        "sCdbStdIO": oCdbWrapper.sCdbIOHTML,
      };
