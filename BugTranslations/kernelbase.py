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
      ], [
        "kernelbase.dll!wil::details::DebugBreak",
      ],
    ],
  ),
  # OOM -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "KERNELBASE.dll!TerminateProcessOnMemoryExhaustion",
      ],
    ],
  ),
];
