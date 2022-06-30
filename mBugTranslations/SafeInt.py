from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # IntegerOverflow -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!SafeIntExceptionHandler<.+>::SafeIntOnOverflow",
      rb".*!msl::utilities::SafeIntErrorPolicy_SafeIntException::SafeIntOnOverflow",
    ],
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"C\+\+:msl::utilities::SafeIntException",
    s0zTranslatedBugTypeId = "SafeInt",
    s0zTranslatedBugDescription = "The application attempted to store an integer value in an integer type that cannot contain this value.",
    s0zTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"SafeInt",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!msl::utilities::SafeInt<.+>::operator\+\+",
    ],
    s0zTranslatedBugTypeId = "IntegerOverflow",
    s0zTranslatedBugDescription = "The application attempted to increase an integer above its maxium value.",
    s0zTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"SafeInt",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!msl::utilities::SafeInt<.+>::operator\-\-",
    ],
    s0zTranslatedBugTypeId = "IntegerUnderflow",
    s0zTranslatedBugDescription = "The application attempted to decrease an integer below its minimum value.",
    s0zTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"SafeInt",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!msl::utilities::details::MultiplicationHelper<.+>::Multiply",
    ],
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!msl::utilities::SafeInt<...>::operator\*=<.+>",
    ],
    s0zTranslatedBugTypeId = "IntegerTruncation",
    s0zTranslatedBugDescription = "The application attempted to store the result of a multiplication in an integer that cannot contain this value.",
    s0zTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"SafeInt",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!msl::utilities::details::LargeIntRegMultiply<.+>::RegMultiply",
    ],
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!msl::utilities::details::LargeIntRegMultiply<.*>::.*",
      rb".*!msl::utilities::details::MultiplicationHelper<.*>::.*",
      rb".*!msl::utilities::SafeInt<...>::operator\*=<.+>",
    ],
    s0zTranslatedBugTypeId = "IntegerTruncation",
    s0zTranslatedBugDescription = "The application attempted to store the result of a multiplication in an integer that cannot contain this value.",
    s0zTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"SafeInt",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!msl::utilities::details::SafeCastHelper<.+>::Cast",
    ],
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!msl::utilities::SafeInt<.+>::SafeInt<.+><.+>",
      rb".*!msl::utilities::SafeInt<.+>::operator=<.+>",
    ],
    s0zTranslatedBugTypeId = "IntegerTruncation",
    s0zTranslatedBugDescription = "The application attempted to store a value in an integer that cannot contain this value.",
    s0zTranslatedSecurityImpact = None,
  ),
];
