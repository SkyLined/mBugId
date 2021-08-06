from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"ucrtbase\.dll!abort",
      rb"ucrtbase\.dll!terminate",
      rb"ucrtbase\.dll!__crt_state_management::wrapped_invoke<.+>",
    ],
  ),
];
