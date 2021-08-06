from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> Assert
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::InduceAbandonment",
    ],
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!Abandonment::AssertionFailed",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::(?:OutOfMemory|CheckAllocation)",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::CheckHRESULT(?:Strict)?",
    ],
    s0zTranslatedBugTypeId = "Assert:HRESULT",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate an unexpected HRESULT was detected.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Arguments
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::InvalidArguments",
    ],
    s0zTranslatedBugTypeId = "Assert:Arguments",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate a function was called with invalid arguments.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Unreachable
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::UnreachableCode",
    ],
    s0zTranslatedBugTypeId = "Assert:Unreachable",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate a supposedly unreachable code path was taken.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Fail
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::Fail",
    ],
    s0zTranslatedBugTypeId = "Assert:Fail",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::InduceHRESULTAbandonment",
    ],
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!Abandonment::CheckHRESULTStrict",
    ],
    s0zTranslatedBugTypeId = "Assert:HRESULT",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate an unexpected HRESULT was detected.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:Deprecated
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::DeprecatedAPI",
    ],
    s0zTranslatedBugTypeId = "Assert:Deprecated",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate a deprecated API was used.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert -> Assert:RequiredQI
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::InduceRequiredQIAbandonment",
    ],
    s0zTranslatedBugTypeId = "Assert:QI",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate a QueryInterface failed.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # FailFast -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"FailFast",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!Abandonment::(?:OutOfMemory|CheckAllocation)",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a Fail Fast exception to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # OOM -> hide irelevant frames
  cBugTranslation(
    srzOriginalBugTypeId = r"OOM",
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!Abandonment::CheckAllocationT<.+>",
    ],
  ),
];
