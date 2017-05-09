from cBugTranslation import cBugTranslation;

# Breakpoint (hide irrelevant frames only)
aoBugTranslations = [];
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalTopStackFrameSymbols = [
    "KERNELBASE.dll!DebugBreak",
  ],
));
