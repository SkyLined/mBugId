from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!wil::details::DebugBreak",
      rb".*!wil::details::in1diag3::Throw_.+",
      rb".*!wil::details::ReportFailure_.+",
      rb".*!wil::details::ThrowResultExceptionInternal",
      rb".*!wil::details::WilDynamicLoadRaiseFailFastException",
      rb".*!wil::details::WilFailFast",
      rb".*!wil::details::WilRaiseFailFastException",
    ],
  ),
  # AppExit -> Assert
  cBugTranslation(
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::ReportFailure",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered a fail fast application exit to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable.",
  ),
  # Assert -> Assert:Win32
  cBugTranslation(
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::(?:ReportFailure|in1diag3::_?FailFast)_Win32",
    ],
    s0zTranslatedBugTypeId = "Assert:Win32",
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::(?:ReportFailure|in1diag3::_?FailFast)_Hr",
    ],
    s0zTranslatedBugTypeId = "Assert:HRESULT",
  ),
  # Assert -> Assert:Unexpected
  cBugTranslation(
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::(?:ReportFailure|in1diag3::_?FailFast)_Unexpected",
    ],
    s0zTranslatedBugTypeId = "Assert:Unexpected",
  ),
  # Assert -> OOM
  cBugTranslation(
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::(?:ReportFailure|in1diag3::_?FailFast)_NullAlloc",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application was unable to allocate enough memory.",
  ),
  # Assert:HRESULT -> OOM
  cBugTranslation(
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::in1diag3::_?FailFast_NullAlloc",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application was unable to allocate enough memory.",
  ),
];
