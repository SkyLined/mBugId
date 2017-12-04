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
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::ReportFailure_Win32",
      ], [
        "*!wil::details::in1diag3::_FailFast_Win32",
      ],
    ],
    sTranslatedBugTypeId = "Assert:Breakpoint",
    sTranslatedBugDescription = "The application triggered a debugger breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # AppExit -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "AppExit",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::ReportFailure",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!wil::details::ReportFailure_Win32",
      ], [
        "*!wil::details::in1diag3::_FailFast_Win32",
      ],
    ],
    sTranslatedBugTypeId = "Assert:AppExit",
    sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this fail fast application exit.",
  ),
  # Assert:Breakpoint -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert:Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::in1diag3::_FailFast_NullAlloc",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a debugger breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
  # Assert:AppExit -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert:AppExit",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::in1diag3::_FailFast_NullAlloc",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this fail fast application exit.",
  ),
  # Assert:AppExit -> Assert:HRESULT
  cBugTranslation(
    sOriginalBugTypeId = "Assert:AppExit",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!wil::details::ReportFailure_Hr",
      ], [
        "*!wil::details::in1diag3::FailFast_Hr",
      ], [
        "*!wil::details::in1diag3::_FailFast_Hr",
      ],
    ],
    sTranslatedBugTypeId = "Assert:HRESULT",
    sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this fail fast application exit.",
  ),
  # Assert:Breakpoint -> Assert:HRESULT
  cBugTranslation(
    sOriginalBugTypeId = "Assert:Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!wil::details::ReportFailure_Hr",
      ], [
        "*!wil::details::in1diag3::FailFast_Hr",
      ], [
        "*!wil::details::in1diag3::_FailFast_Hr",
      ],
    ],
    sTranslatedBugTypeId = "Assert:HRESULT",
    sTranslatedBugDescription = "The application triggered a breakpoint exception to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint exception.",
  ),
  # Assert:AppExit -> Assert:Unexpected
  cBugTranslation(
    sOriginalBugTypeId = "Assert:AppExit",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::in1diag3::FailFast_Unexpected",
    ],
    sTranslatedBugTypeId = "Assert:Unexpected",
    sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this fail fast application exit.",
  ),
  # Assert:Breakpoint -> Assert:Unexpected
  cBugTranslation(
    sOriginalBugTypeId = "Assert:Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "*!wil::details::in1diag3::FailFast_Unexpected",
    ],
    sTranslatedBugTypeId = "Assert:Unexpected",
    sTranslatedBugDescription = "The application triggered a breakpoint exception to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint exception.",
  ),
];
