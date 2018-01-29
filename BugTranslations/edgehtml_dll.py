from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "edgehtml.dll!Abandonment::InduceAbandonment",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "edgehtml.dll!Abandonment::AssertionFailed",
      ],
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasOriginalTopStackFrameSymbols = [
      [
        "edgehtml.dll!Abandonment::OutOfMemory",
      ], [
        "edgehtml.dll!Abandonment::CheckAllocation",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasOriginalTopStackFrameSymbols = [
      [
        "edgehtml.dll!Abandonment::CheckHRESULT",
      ], [
        "edgehtml.dll!Abandonment::CheckHRESULTStrict",
      ],
    ],
    sTranslatedBugTypeId = "Assert:HRESULT",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an unexpected HRESULT was detected.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Arguments
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "edgehtml.dll!Abandonment::InvalidArguments",
    ],
    sTranslatedBugTypeId = "Assert:Arguments",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate a function was called with invalid arguments.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Unreachable
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "edgehtml.dll!Abandonment::UnreachableCode",
    ],
    sTranslatedBugTypeId = "Assert:Unreachable",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate a supposedly unreachable code path was taken.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Fail
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "edgehtml.dll!Abandonment::Fail",
    ],
    sTranslatedBugTypeId = "Assert:Fail",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "edgehtml.dll!Abandonment::InduceHRESULTAbandonment",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "edgehtml.dll!Abandonment::CheckHRESULTStrict",
      ],
    ],
    sTranslatedBugTypeId = "Assert:HRESULT",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an unexpected HRESULT was detected.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Deprecated
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "edgehtml.dll!Abandonment::DeprecatedAPI",
    ],
    sTranslatedBugTypeId = "Assert:Deprecated",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate a deprecated API was used.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:RequiredQI
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "edgehtml.dll!Abandonment::InduceRequiredQIAbandonment",
    ],
    sTranslatedBugTypeId = "Assert:QI",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate a QueryInterface failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # FailFast -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "FailFast",
    aasOriginalTopStackFrameSymbols = [
      [
        "edgehtml.dll!Abandonment::OutOfMemory",
      ], [
        "edgehtml.dll!Abandonment::CheckAllocation",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a Fail Fast exception to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # OOM -> hide irelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "edgehtml.dll!Abandonment::CheckAllocationT<...>",
      ], [
        "edgehtml.dll!Streams::Chunk<...>::InternalAlloc",
      ],
    ],
  ),
];
