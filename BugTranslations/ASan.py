from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint --> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "syzyasan_rtl.dll!base::debug::BreakDebugger",
      "syzyasan_rtl.dll!agent::asan::StackCaptureCache::AllocateCachePage",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "ASan triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!__sanitizer::internal__exit",
        "*!__sanitizer::Die",
        "*!__asan::AsanCheckFailed",
        "*!__sanitizer::CheckFailed",
        "*!__sanitizer::ReportAllocatorCannotReturnNull",
      ], [
        "*!__sanitizer::internal__exit",
        "*!__sanitizer::Die",
        "*!__asan::AsanCheckFailed",
        "*!__sanitizer::CheckFailed",
        "*!__sanitizer::ReportMmapFailureAndDie",
      ], [
        "*!__sanitizer::internal__exit",
        "*!__sanitizer::ReportMmapFailureAndDie",
      ], [
        "*!__sanitizer::internal__exit",
        "*!__sanitizer::Abort",
        "*!__asan::ReserveShadowMemoryRange",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "ASan triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!__sanitizer::internal__exit",
        "*!__sanitizer::Die",
        "*!__asan::ScopedInErrorReport::~ScopedInErrorReport",
        "*!__asan::ReportGenericError",
        "*!__asan_report_load1",
      ],
    ],
    sTranslatedBugTypeId = "ASan",
    sTranslatedBugDescription = "ASan triggered a breakpoint to indicate it detected something.",
    sTranslatedSecurityImpact = "This may indicate an exploitable security issue",
  ),
  # OOM (hide irrelevant frames only)
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!__asan::Allocator::Allocate",
      ], [
        "*!__asan::asan_malloc",
      ], [
        "*!__sanitizer::CombinedAllocator<...>::Allocate",
      ], [
        "*!__sanitizer::DumpProcessMap",
      ], [
        "*!__sanitizer::internal_strdup",
      ], [
        "*!__sanitizer::InternalAlloc",
      ], [
        "*!__sanitizer::LargeMmapAllocator<...>::Allocate",
      ], [
        "*!__sanitizer::LargeMmapAllocator<...>::ReturnNullOrDieOnOOM",
      ], [
        "*!__sanitizer::ListOfModules::init",
      ], [
        "*!__sanitizer::LoadedModule::set",
      ], [
        "*!__sanitizer::MmapAlignedOrDie",
      ], [
        "*!__sanitizer::MmapOrDieOnFatalError",
      ], [
        "*!__sanitizer::RawInternalAlloc",
      ], [
        "*!__sanitizer::ReportMmapFailureAndDie",
      ], [
        "*!__sanitizer::SizeClassAllocator32<...>::AllocateBatch",
      ], [
        "*!__sanitizer::SizeClassAllocator32<...>::AllocateRegion",
      ], [
        "*!__sanitizer::SizeClassAllocator32<...>::PopulateFreeList",
      ], [
        "*!__sanitizer::SizeClassAllocator32LocalCache<...>::Allocate",
      ], [
        "*!__sanitizer::SizeClassAllocator32LocalCache<...>::Refill",
      ], [
        "*!agent::asan::heap_managers::BlockHeapManager::Allocate",
      ], [
        "*!agent::asan::heap_managers::BlockHeapManager::Free",
      ], [
        "*!agent::asan::StackCaptureCache::GetStackCapture",
      ], [
        "*!agent::asan::StackCaptureCache::SaveStackTrace",
      ], [
        "*!agent::asan::WindowsHeapAdapter::HeapAlloc",
      ], [
        "*!agent::asan::WindowsHeapAdapter::HeapReAlloc",
      ], [
        "*!asan_HeapAlloc",
      ], [
        "*!asan_HeapReAlloc",
      ],
    ],
  ),
];