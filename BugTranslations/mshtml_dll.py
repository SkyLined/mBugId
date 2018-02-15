from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "mshtml.dll!ReportFatalException",
        "mshtml.dll!MarkStack_OOM_fatal_error",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "mshtml.dll!Memory::HeapBucketT<...>::SnailAlloc",
      ], [
        "mshtml.dll!Memory::Recycler::AllocWithAttributesInlined<...>",
      ], [
        "mshtml.dll!Memory::Recycler::CollectNow<...>",
      ], [
        "mshtml.dll!Memory::Recycler::EndMark",
      ], [
        "mshtml.dll!Memory::Recycler::EndMarkCheckOOMRescan",
      ], [
        "mshtml.dll!Memory::Recycler::EndMarkOnLowMemory",
      ], [
        "mshtml.dll!Memory::Recycler::FinishConcurrentCollect",
      ], [
        "mshtml.dll!Memory::Recycler::FinishMark",
      ], [
        "mshtml.dll!Memory::Recycler::NoThrowAllocImplicitRoot",
      ], [
        "mshtml.dll!Memory::Recycler::RealAllocFromBucket<...>",
      ], [
        "mshtml.dll!Memory::Recycler::RootMark",
      ], [
        "mshtml.dll!MemoryProtection::HeapAlloc<...>",
      ]
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
];