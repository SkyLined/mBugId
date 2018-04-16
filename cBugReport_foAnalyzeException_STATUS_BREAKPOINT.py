def cBugReport_foAnalyzeException_STATUS_BREAKPOINT(oBugReport, oProcess, oException):
  oProcess.oCdbWrapper.oASanErrorDetector.fAddInformationToBugReport(oBugReport, oProcess);
  return oBugReport;
