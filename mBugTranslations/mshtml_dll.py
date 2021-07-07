from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azsrbAppliesOnlyToTopStackFrame = [
      rb"mshtml\.dll!ReportFatalException",
      rb"mshtml\.dll!MarkStack_OOM_fatal_error",
    ],
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"mshtml\.dll!Memory::.*",
      rb"mshtml\.dll!MemoryProtection::.*",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
];