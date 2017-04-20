from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Breakpoint -> HeapCorrupt
for asBreakpoint_HeapCorrupt_Stack in [
  [
    "ntdll.dll!RtlReportCriticalFailure",
    "ntdll.dll!RtlpHeapHandleError",
  ], [
    "ntdll.dll!RtlpBreakPointHeap",
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalStackTopFrameAddresses = asBreakpoint_HeapCorrupt_Stack,
    sTranslatedBugTypeId = "HeapCorrupt",
    sTranslatedBugDescription = "A breakpoint was triggered to indicate heap corruption was detected",
    sTranslatedSecurityImpact = "This is probably an exploitable security issue",
  ));
