from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # AVE@NULL -> Assert
  cBugTranslation(
    srzOriginalBugTypeId = r"AVE@NULL",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!v8::base::OS::Abort",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application caused an access violation by calling NULL to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = None,
  ),
  # AVE@NULL -> Assert
  cBugTranslation(
    srzOriginalBugTypeId = r"AVE@NULL",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!V8_Fatal",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application caused an access violation by calling NULL to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = None,
  ),
  # Assert -> ignore functions
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!V8_Fatal",
      rb".*!v8::base::OS::Abort",
      rb".*!v8::MaybeLocal<.+>::ToLocalChecked",
      rb".*!v8::Utils::ReportApiFailure",
      rb".*!v8::Utils::ApiCheck",
      rb".*!v8::V8::ToLocalEmpty",
      rb".*!v8::MaybeLocal",
    ],
  ),
  # Assert -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!v8::internal::V8::FatalProcessOutOfMemory",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application caused a fatal exception to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # Assert -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!v8::Utils::ReportOOMFailure",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application caused a fatal exception to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
];
