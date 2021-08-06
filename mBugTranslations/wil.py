import re;

from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!wil::details::DebugBreak",
      rb".*!wil::details::in1diag3::Throw_Hr",
      rb".*!wil::details::ThrowResultExceptionInternal",
      rb".*!wil::details::WilDynamicLoadRaiseFailFastException",
      rb".*!wil::details::WilFailFast",
      rb".*!wil::details::WilRaiseFailFastException",
    ],
  ),
  # Breakpoint -> Assert
  cBugTranslation(
   srzOriginalBugTypeId = "Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::ReportFailure",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered a debugger breakpoint to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # AppExit -> Assert
  cBugTranslation(
   srzOriginalBugTypeId = "AppExit",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::ReportFailure",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered a fail fast application exit to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this fail fast application exit.",
  ),
  # Assert -> Assert:Win32
  cBugTranslation(
   srzOriginalBugTypeId = "Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::(?:ReportFailure_Win32|in1diag3::_?FailFast_Win32)",
    ],
    s0zTranslatedBugTypeId = "Assert:Win32",
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
   srzOriginalBugTypeId = "Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::(?:ReportFailure_Hr|in1diag3::_?FailFast_Hr)",
    ],
    s0zTranslatedBugTypeId = "Assert:HRESULT",
  ),
  # Assert -> Assert:Unexpected
  cBugTranslation(
   srzOriginalBugTypeId = "Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::(?:ReportFailure_Unexpected|in1diag3::_?FailFast_Unexpected)",
    ],
    s0zTranslatedBugTypeId = "Assert:Unexpected",
  ),
  # Assert -> OOM
  cBugTranslation(
   srzOriginalBugTypeId = "Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::in1diag3::_?FailFast_NullAlloc",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application was unable to allocate enough memory.",
  ),
  # Assert:HRESULT -> OOM
  cBugTranslation(
   srzOriginalBugTypeId = "Assert:HRESULT",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!wil::details::in1diag3::_?FailFast_NullAlloc",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application was unable to allocate enough memory.",
  ),
];
