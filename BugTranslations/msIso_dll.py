from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Assert -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "msiso.dll!CIsoMalloc::_InitializeEntry",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "msIso.dll!CIsoScope::_AllocArtifact",
      ], [
        "msIso.dll!CIsoSList::AllocArtifact",
      ], [
        "msIso.dll!CIsoScope::_AllocMessageBuffer",
      ], [
        "msIso.dll!CIsoScope::AllocMessageBuffer",
      ], [
        "msIso.dll!IsoAllocMessageBuffer",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
];
