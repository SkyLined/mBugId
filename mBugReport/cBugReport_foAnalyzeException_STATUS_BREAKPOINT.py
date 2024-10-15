def cBugReport_foAnalyzeException_STATUS_BREAKPOINT(oBugReport, oProcess, oWindowsAPIThread, oException):
  oProcess.oCdbWrapper.oASanErrorDetector.fAddInformationToBugReport(oBugReport, oProcess, oWindowsAPIThread);
  return oBugReport;
