import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
# AVE@NULL -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "AVE@NULL",
    asOriginalTopStackFrameSymbols = [
      "0x0",
      "*!v8::base::OS::Abort",
      "*!v8::Utils::ReportApiFailure",
      "*!v8::Utils::ApiCheck",
      "*!v8::internal::V8::FatalProcessOutOfMemory",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application caused an access violation by calling NULL to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # Assert -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    asOriginalTopStackFrameSymbols = [
      "*!v8::internal::V8::FatalProcessOutOfMemory",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # AVE@NULL -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "AVE@NULL",
    asOriginalTopStackFrameSymbols = [
      "*!V8_Fatal",
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application caused an access violation by calling NULL to indicate an assertion failed.",
    sTranslatedSecurityImpact = None,
  ),
  # Assert -> ignore functions
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!v8::Utils::ReportApiFailure",
      ], [
        "*!v8::Utils::ApiCheck",
      ], [
        "*!v8::V8::ToLocalEmpty",
      ], [
        "*!v8::MaybeLocal",
      ],
    ],
  ),
];
