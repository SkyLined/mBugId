from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"conhost\.exe!o_terminate",
      rb"conhost\.exe!_scrt_unhandled_exception_filter",
    ],
  ),
];
