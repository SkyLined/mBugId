from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"clr\.dll!RaiseTheExceptionInternalOnly",
      rb"clr\.dll!IL_Throw",
    ],
  ),
];