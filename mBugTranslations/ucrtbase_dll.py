from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"ucrtbase\.dll!abort",
      rb"ucrtbase\.dll!terminate",
      rb"ucrtbase\.dll!__crt_state_management::wrapped_invoke<.+>",
    ],
  ),
];
