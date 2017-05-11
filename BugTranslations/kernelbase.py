from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # The following frames are always irrelevant to bugs:
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
];
