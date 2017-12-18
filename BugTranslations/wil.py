from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::DebugBreak",
      ],
    ],
  ),
  # Breakpoint -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::ReportFailure",
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a debugger breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # AppExit -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "AppExit",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::ReportFailure",
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this fail fast application exit.",
  ),
  # Assert -> Assert:Win32
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!wil::details::ReportFailure_Win32",
      ], [
        "*!wil::details::in1diag3::FailFast_Win32",
      ], [
        "*!wil::details::in1diag3::_FailFast_Win32",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::in1diag3::FailFast_Win32",
      ], [
        "*!wil::details::in1diag3::_FailFast_Win32",
      ],
    ],
    sTranslatedBugTypeId = "Assert:Win32",
  ),
  # Assert -> Assert:HRESULT
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!wil::details::ReportFailure_Hr",
      ], [
        "*!wil::details::in1diag3::FailFast_Hr",
      ], [
        "*!wil::details::in1diag3::_FailFast_Hr",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::in1diag3::FailFast_Hr",
      ], [
        "*!wil::details::in1diag3::_FailFast_Hr",
      ],
    ],
    sTranslatedBugTypeId = "Assert:HRESULT",
  ),
  # Assert -> Assert:Unexpected
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!wil::details::ReportFailure_Unexpected",
      ], [
        "*!wil::details::in1diag3::FailFast_Unexpected",
      ], [
        "*!wil::details::in1diag3::_FailFast_Unexpected",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::in1diag3::FailFast_Unexpected",
      ], [
        "*!wil::details::in1diag3::_FailFast_Unexpected",
      ],
    ],
    sTranslatedBugTypeId = "Assert:Unexpected",
  ),
  # Assert -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::in1diag3::_FailFast_NullAlloc",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::in1diag3::FailFast_IfNullAlloc",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application was unable to allocate enough memory.",
  ),
  # Assert:HRESULT -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert:HRESULT",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::in1diag3::_FailFast_NullAlloc",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::in1diag3::FailFast_IfNullAlloc",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application was unable to allocate enough memory.",
  ),
];
