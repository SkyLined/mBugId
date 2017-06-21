import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # These frames are never relevant
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "ntdll.dll!DbgBreakPoint",
      ],
    ],
  ),
  # Breakpoint -> HeapCorrupt
  cBugTranslation(
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
  ),
  # OOM, HeapCorrupt, DoubleFree, MisalignedFree, OOBW -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = re.compile(r"^(OOM|HeapCorrupt|DoubleFree\[.*|MisalignedFree\[.*|OOBW\[.*)$"),
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "ntdll.dll!RtlAllocateHeap",
      ], [
        "ntdll.dll!RtlDebugAllocateHeap",
      ], [
        "ntdll.dll!RtlDebugFreeHeap",
      ], [
        "ntdll.dll!RtlFreeHeap",
      ], [
        "ntdll.dll!RtlpAllocateHeap",
      ], [
        "ntdll.dll!RtlpAllocateHeapInternal",
      ], [
        "ntdll.dll!RtlpAllocateHeapRaiseException",
      ], [
        "ntdll.dll!RtlpFreeHeap",
      ],
    ],
  ),
];