from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"kernelbase\.dll!DebugBreak",
      rb"kernelbase\.dll!RaiseException",
      rb"kernelbase\.dll!RaiseFailFastException",
      rb"kernelbase\.dll!UnhandledExceptionFilter",
      rb"kernelbase\.dll!TerminateProcessOnMemoryExhaustion",
      rb"kernelbase\.dll!LocalFree",
    ],
  ),
];
