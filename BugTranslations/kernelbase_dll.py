from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!DebugBreak",
      ], [
        "kernelbase.dll!RaiseException",
      ], [
        "kernelbase.dll!RaiseFailFastException",
      ],
    ],
  ),
  # OOM -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!TerminateProcessOnMemoryExhaustion",
      ],
    ],
  ),
];
