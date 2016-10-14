# Some fail fast exceptions may indicate an out-of-memory bug:
dtxBugTranslations = {
  "OOM": (
    "The process triggered a fail-fast exception to indicate it was unable to allocate enough memory",
    None,
    [
      [ # Edge
        "EDGEHTML.dll!Abandonment::OutOfMemory",
      ],
    ],
  ),
  "Assert": (
    "An assertion failed",
    None,
    [
      [ # Edge
        "EDGEHTML.dll!Abandonment::CheckHRESULT",
      ],
      [
        "EDGEHTML.dll!Abandonment::CheckHRESULTStrict",
      ],
      [
        "EDGEHTML.dll!Abandonment::InvalidArguments",
      ],
    ],
  ),
};

def cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION(oBugReport, oCdbWrapper, oException):
  # cdb does not known this exception and reports "Unknown exception (code 0xC0000602)" as the description.
  oBugReport.sBugDescription = "Fail fast exception (code 0x%X)" % oException.uCode;
  oBugReport = oBugReport.foTranslate(dtxBugTranslations);
  return oBugReport;

