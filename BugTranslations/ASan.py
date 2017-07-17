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
  # Breakpoint --> ASan
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
  # IllegalInstruction --> ASan
  cBugTranslation(
    sOriginalBugTypeId = "IllegalInstruction",
    asOriginalTopStackFrameSymbols = [
      "*!__sanitizer::Trap",
    ],
    sTranslatedBugTypeId = "ASan",
    sTranslatedBugDescription = "ASan triggered an illegal instruction to indicate it detected an issue.",
    sTranslatedSecurityImpact = "The security implications of this issue are unknown",
  ),
  # ASan -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "Asan",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!__asan::AsanCheckFailed",
      ], [
        "*!__sanitizer::BlockingMutex::Lock",
      ], [
        "*!__sanitizer::CheckFailed",
      ], [
        "*!__sanitizer::GenericScopedLock<...>::{ctor}",
      ], [
        "*!__sanitizer::StackTrace::Print",
      ], [
        "*!__sanitizer::Symbolizer::SymbolizePC",
      ],
    ],
  ),
  # ASan --> ASan:Error
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
  # ASan --> OOM
  cBugTranslation(
    sOriginalBugTypeId = "ASan",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!__sanitizer::ReportAllocatorCannotReturnNull",
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