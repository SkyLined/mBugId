def cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION(oBugReport, oProcess, oException):
  # cdb does not known this exception and reports "Unknown exception (code 0xC0000602)" as the description.
  oBugReport.sBugDescription = "Fail fast exception (code 0x%X)" % oException.uCode;
  return oBugReport;
