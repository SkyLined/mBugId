from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Assert -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"edgecontent\.dll!`anonymous namespace'::MemoryLimitWatchdogThreadProc",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
];
