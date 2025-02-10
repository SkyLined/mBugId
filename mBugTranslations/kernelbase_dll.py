from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      # There are a lot of helper functions that clutter the stack without
      # providing insight into the issue. These are all hidden by BugId:
      rb"kernelbase\.dll!DebugBreak",
      rb"kernelbase\.dll!FindClose",
      rb"kernelbase\.dll!LocalFree",
      rb"kernelbase\.dll!Raise.*Exception",
      rb"kernelbase\.dll!UnhandledExceptionFilter",
      rb"kernelbase\.dll!TerminateProcessOnMemoryExhaustion",
    ],
  ),
];
