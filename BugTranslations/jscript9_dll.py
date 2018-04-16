from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "jscript9.dll!ReportFatalException",
      "jscript9.dll!JavascriptDispatch_OOM_fatal_error",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
];
