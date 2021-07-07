from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> ignore stack
  cBugTranslation(
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"jscript9\.dll!ReportFatalException",
    ],
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azsrbAppliesOnlyToTopStackFrame = [
      rb"jscript9\.dll!JavascriptDispatch_OOM_fatal_error",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
];
