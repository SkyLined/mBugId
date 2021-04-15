import re;
from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      re.compile(r".*!Abandonment::InduceAbandonment"),
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile(r".*!Abandonment::AssertionFailed"),
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
        re.compile(r".*!Abandonment::OutOfMemory"),
      ], [
        re.compile(r".*!Abandonment::CheckAllocation"),
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
        re.compile(r".*!Abandonment::CheckHRESULT"),
      ], [
        re.compile(r".*!Abandonment::CheckHRESULTStrict"),
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
      re.compile(r".*!Abandonment::InvalidArguments"),
    ],
    sTranslatedBugTypeId = "Assert:Arguments",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate a function was called with invalid arguments.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Unreachable
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      re.compile(r".*!Abandonment::UnreachableCode"),
    ],
    sTranslatedBugTypeId = "Assert:Unreachable",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate a supposedly unreachable code path was taken.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Fail
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      re.compile(r".*!Abandonment::Fail"),
    ],
    sTranslatedBugTypeId = "Assert:Fail",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      re.compile(r".*!Abandonment::InduceHRESULTAbandonment"),
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile(r".*!Abandonment::CheckHRESULTStrict"),
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
      re.compile(r".*!Abandonment::DeprecatedAPI"),
    ],
    sTranslatedBugTypeId = "Assert:Deprecated",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate a deprecated API was used.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:RequiredQI
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      re.compile(r".*!Abandonment::InduceRequiredQIAbandonment"),
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
        re.compile(r".*!Abandonment::OutOfMemory"),
      ], [
        re.compile(r".*!Abandonment::CheckAllocation"),
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
        re.compile(r".*!Abandonment::CheckAllocationT<...>"),
      ],
    ],
  ),
];
