from .cBugTranslation import cBugTranslation;
from .rHeapRelatedBugIds import rHeapRelatedBugIds;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "clr.dll!RaiseTheExceptionInternalOnly",
      ], [
        "clr.dll!IL_Throw",
      ],
    ],
  ),
];