import re;
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
    asOriginalTopStackFrameSymbols = [
      "*!__sanitizer::internal__exit",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!__sanitizer::Die",
      ],
    ],
    sTranslatedBugTypeId = "ASan",
    sTranslatedBugDescription = "ASan triggered a breakpoint to indicate it detected an issue.",
    sTranslatedSecurityImpact = "The security implications of this issue are unknown",
  ),
  cBugTranslation(
    sOriginalBugTypeId = "ASan",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!__asan::AsanCheckFailed",
        "*!__sanitizer::CheckFailed",
        "*!__sanitizer::ReportAllocatorCannotReturnNull",
      ], [
        "*!__asan::AsanCheckFailed",
        "*!__sanitizer::CheckFailed",
        "*!__sanitizer::ReportMmapFailureAndDie",
      ], [
        "*!__sanitizer::ReportMmapFailureAndDie",
      ], [
        "*!__sanitizer::Abort",
        "*!__asan::ReserveShadowMemoryRange",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "ASan triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "ASan",
    asOriginalTopStackFrameSymbols = [
      "*!__asan::ScopedInErrorReport::~ScopedInErrorReport",
      "*!__asan::ReportGenericError",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile("^.*!__asan_report_(load|store)\d+$"),
      ],
    ],
    sTranslatedBugTypeId = "ASan:Error",
    sTranslatedBugDescription = "ASan triggered a breakpoint to indicate it detected something.",
    sTranslatedSecurityImpact = "The security implications of this issue are unknown",
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