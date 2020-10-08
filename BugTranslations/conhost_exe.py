from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "conhost.exe!o_terminate",
      ], [
        "conhost.exe!_scrt_unhandled_exception_filter",
      ],
    ],
  ),
];
