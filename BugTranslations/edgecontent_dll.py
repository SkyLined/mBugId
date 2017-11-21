from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Assert -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasOriginalTopStackFrameSymbols = [
      [
        "edgecontent.dll!`anonymous namespace'::MemoryLimitWatchdogThreadProc",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
];
