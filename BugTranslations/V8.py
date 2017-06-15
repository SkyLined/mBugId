import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# AVE@NULL -> OOM
aoBugTranslations.append(cBugTranslation(
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
));
# Assert -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "*!v8::internal::V8::FatalProcessOutOfMemory",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
# AVE@NULL -> Assert
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "AVE@NULL",
  asOriginalTopStackFrameSymbols = [
    "*!V8_Fatal",
  ],
  sTranslatedBugTypeId = "Assert",
  sTranslatedBugDescription = "The application caused an access violation by calling NULL to indicate an assertion failed.",
  sTranslatedSecurityImpact = None,
));
