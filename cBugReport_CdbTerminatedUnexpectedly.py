from sBlockHTMLTemplate import sBlockHTMLTemplate;
from sReportHTMLTemplate import sReportHTMLTemplate;
from sVersion import sVersion;

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
    oBugReport.sBugLocation = None;
    oBugReport.sBugSourceLocation = None;
    oBugReport.asVersionInformation = ["BugId: %s" % sVersion];
    
    if oCdbWrapper.bGenerateReportHTML:
      # Turn cdb output into formatted HTML. It is separated into blocks, one for the initial cdb output and one for each
      # command executed.
      sCdbStdIOHTML = '<hr/>'.join(oCdbWrapper.asCdbStdIOBlocksHTML);
      oCdbWrapper.asCdbStdIOBlocksHTML = [""];
      asBlocksHTML = [];
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application and cdb output log",
        "sCollapsed": "Collapsed",
        "sContent": sCdbStdIOHTML
      });
      # Create HTML details
      oBugReport.sReportHTML = sReportHTMLTemplate % {
        "sId": oCdbWrapper.fsHTMLEncode(oBugReport.sId),
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation or "Unknown"),
        "sBugDescription": oCdbWrapper.fsHTMLEncode(oBugReport.sBugDescription),
        "sBinaryVersion": "Not available",
        "sOptionalSource": "",
        "sSecurityImpact": oBugReport.sSecurityImpact and \
              '<span class="SecurityImpact">%s</span>' % oCdbWrapper.fsHTMLEncode(oBugReport.sSecurityImpact) or "None",
        "sOptionalCommandLine": "",
        "sBugIdVersion": sVersion,
        "sBlocks": "\r\n".join(asBlocksHTML),
        "sCdbStdIO": sCdbStdIOHTML,
      };
