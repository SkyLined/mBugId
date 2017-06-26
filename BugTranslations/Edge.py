from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Breakpoint -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  aasOriginalTopStackFrameSymbols = [
    [
      "chakra.dll!ReportFatalException",
      "chakra.dll!MarkStack_OOM_fatal_error",
    ], [
      "chakra.dll!ReportFatalException",
      "chakra.dll!JavascriptDispatch_OOM_fatal_error",
    ],
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
# Breakpoint -> Assert
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  aasOriginalTopStackFrameSymbols = [
    [
      "EDGEHTML.dll!Abandonment::InduceAbandonment",
    ], [
      "KERNELBASE.dll!RaiseException",
      "EDGEHTML.dll!Abandonment::InduceAbandonment",
    ],
  ],
  sTranslatedBugTypeId = "Assert",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# AppExit -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "AppExit",
  asOriginalTopStackFrameSymbols = [
    "*!wil::details::ReportFailure",
    "*!wil::details::ReportFailure_Hr",
    "*!wil::details::in1diag3::_FailFast_NullAlloc",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# AppExit -> Assert
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "AppExit",
  asOriginalTopStackFrameSymbols = [
    "*!wil::details::ReportFailure",
    "*!wil::details::ReportFailure_Hr",
  ],
  aasAdditionalIrrelevantStackFrameSymbols = [
    [
      "*!wil::details::in1diag3::FailFast_Hr",
    ],
  ],
  sTranslatedBugTypeId = "Assert",
  sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate an assertion failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# Assert -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "EDGEHTML.dll!Abandonment::OutOfMemory",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
# Breakpoint -> Assert:HRESULT
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  aasOriginalTopStackFrameSymbols = [
    [
      "EDGEHTML.dll!Abandonment::CheckHRESULT",
    ], [
      "EDGEHTML.dll!Abandonment::CheckHRESULTStrict",
    ],
  ],
  sTranslatedBugTypeId = "Assert:HRESULT",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an unexpected HRESULT was detected.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# Breakpoint -> Assert:Arguments
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "EDGEHTML.dll!Abandonment::InvalidArguments",
  ],
  sTranslatedBugTypeId = "Assert:Arguments",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate a function was called with invalid arguments.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# Assert -> Assert:Unreachable
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "EDGEHTML.dll!Abandonment::UnreachableCode",
  ],
  sTranslatedBugTypeId = "Assert:Unreachable",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate a supposedly unreachable code path was taken.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# Assert -> Assert:Fail
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "EDGEHTML.dll!Abandonment::Fail",
  ],
  sTranslatedBugTypeId = "Assert:Fail",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# Assert -> Assert:HRESULT
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "EDGEHTML.dll!Abandonment::InduceHRESULTAbandonment",
  ],
  aasAdditionalIrrelevantStackFrameSymbols = [
    [
      "EDGEHTML.dll!Abandonment::CheckHRESULTStrict",
    ],
  ],
  sTranslatedBugTypeId = "Assert:HRESULT",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an unexpected HRESULT was detected.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# Assert -> Assert:Deprecated
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "EDGEHTML.dll!Abandonment::DeprecatedAPI",
  ],
  sTranslatedBugTypeId = "Assert:Deprecated",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate a deprecated API was used.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# Assert -> Assert:RequiredQI
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "edgehtml.dll!Abandonment::InduceRequiredQIAbandonment",
  ],
  sTranslatedBugTypeId = "Assert:QI",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate a QueryInterface failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# FailFast -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "FailFast",
  asOriginalTopStackFrameSymbols = [
    "EDGEHTML.dll!Abandonment::OutOfMemory",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a Fail Fast exception to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
