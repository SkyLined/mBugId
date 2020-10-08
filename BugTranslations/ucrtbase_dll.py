from .cBugTranslation import cBugTranslation;
from .rHeapRelatedBugIds import rHeapRelatedBugIds;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "ucrtbase.dll!abort",
      ], [
        "ucrtbase.dll!terminate",
      ], [
        "ucrtbase.dll!__crt_state_management::wrapped_invoke<void (__cdecl*)(void),void>",
      ],
    ],
  ),
];
