from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"clr\.dll!RaiseTheExceptionInternalOnly",
      rb"clr\.dll!IL_Throw",
    ],
  ),
];