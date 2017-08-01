def cBugReport_foAnalyzeException_STATUS_NO_MEMORY(oBugReport, oProcess, oException):
  oBugReport.sBugDescription = "An exception was raised because the program was unable to allocate enough memory";
  return oBugReport;
