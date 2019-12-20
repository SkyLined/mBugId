from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # IntegerOverflow -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "IntegerOverflow",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!SafeIntExceptionHandler<...>::SafeIntOnOverflow",
      ],
    ],
  ),
  cBugTranslation(
    sOriginalBugTypeId = "C++:msl::utilities::SafeIntException",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!msl::utilities::SafeIntErrorPolicy_SafeIntException::SafeIntOnOverflow",
      ],
    ],
    sTranslatedBugTypeId = "SafeInt",
    sTranslatedBugDescription = "The application attempted to store an integer value in an integer type that cannot contain this value.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "SafeInt",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!msl::utilities::SafeInt<...>::operator++",
      ],
    ],
    sTranslatedBugTypeId = "IntegerOverflow",
    sTranslatedBugDescription = "The application attempted to increase an integer above its maxium value.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "SafeInt",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!msl::utilities::SafeInt<...>::operator--",
      ],
    ],
    sTranslatedBugTypeId = "IntegerOverflow",
    sTranslatedBugDescription = "The application attempted to decrease an integer below its minimum value.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "SafeInt",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!msl::utilities::details::MultiplicationHelper<...>::Multiply",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!msl::utilities::SafeInt<...>::operator*=<...>",
      ],
    ],
    sTranslatedBugTypeId = "IntegerOverflow",
    sTranslatedBugDescription = "The application attempted to store the result of a multiplication in an integer that cannot contain this value.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "SafeInt",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!msl::utilities::details::SafeCastHelper<...>::Cast",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!msl::utilities::SafeInt<...>::SafeInt<...><...>",
      ], [
        "*!msl::utilities::SafeInt<...>::operator=<...>",
      ],
    ],
    sTranslatedBugTypeId = "IntegerTruncation",
    sTranslatedBugDescription = "The application attempted to store a value in an integer that cannot contain this value.",
    sTranslatedSecurityImpact = None,
  ),
];
