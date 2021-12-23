def cBugReport_foAnalyzeException_STATUS_BREAKPOINT(oBugReport, oProcess, oThread, oException):
  oProcess.oCdbWrapper.oASanErrorDetector.fAddInformationToBugReport(oBugReport, oProcess, oThread);
  return oBugReport;
