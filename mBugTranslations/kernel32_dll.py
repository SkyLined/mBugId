from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"kernel32\.dll!RaiseExceptionStub",
      rb"kernel32\.dll!HeapFreeStub",
    ],
  ),
];
