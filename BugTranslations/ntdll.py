from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Breakpoint -> HeapCorrupt
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  aasOriginalTopStackFrameSymbols = [
    [
      "ntdll.dll!RtlReportCriticalFailure",
      "ntdll.dll!RtlpHeapHandleError",
    ], [
      "ntdll.dll!RtlpBreakPointHeap",
    ],
  ],
  sTranslatedBugTypeId = "HeapCorrupt",
  sTranslatedBugDescription = "A breakpoint was triggered to indicate heap corruption was detected",
  sTranslatedSecurityImpact = "This is probably an exploitable security issue",
));
