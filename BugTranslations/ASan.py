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
    sOriginalBugTypeId = re.compile("ASan(:.+)?"),
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile("^.*!__asan_report_(load|store)\d+$"),
      ], [
        "*!__asan_unhandled_exception_filter",
      ], [
        "*!__asan::AsanCheckFailed",
      ], [
        "*!__asan::ScopedInErrorReport::~ScopedInErrorReport",
      ], [
        "*!__asan::ReportDeadlySignal",
      ], [
        "*!__asan::ReportGenericError",
      ], [
        "*!__sanitizer::BlockingMutex::Lock",
      ], [
        "*!__sanitizer::CheckFailed",
      ], [
        "*!__sanitizer::Die",
      ], [
        "*!__sanitizer::GenericScopedLock<...>::{ctor}",
      ], [
        "*!__sanitizer::internal__exit",
      ], [
        "*!__sanitizer::StackTrace::Print",
      ], [
        "*!__sanitizer::Symbolizer::SymbolizePC",
      ],
    ],
  ),
  # ASan --> OOM
  cBugTranslation(
    sOriginalBugTypeId = "ASan",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!__sanitizer::ReportAllocatorCannotReturnNull",
      ], [
        "*!__sanitizer::ReturnNullOrDieOnFailure::OnOOM",
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
        re.compile(".*!__sanitizer::LargeMmapAllocator<...>::(Allocate|ReturnNullOrDieOnOOM)"),
      ], [
        "*!__sanitizer::ListOfModules::init",
      ], [
        "*!__sanitizer::LoadedModule::set",
      ], [
        re.compile(".*!__sanitizer::Mmap(Aligned)?OrDie(OnFatalError)?"),
      ], [
        "*!__sanitizer::RawInternalAlloc",
      ], [
        "*!__sanitizer::ReportMmapFailureAndDie",
      ], [
        re.compile(".*!__sanitizer::SizeClassAllocator32(LocalCache)?<...>::(Allocate(Batch|Region)?|PopulateFreeList|Refill)"),
      ], [
        re.compile(".*!agent::asan::heap_managers::BlockHeapManager::(Allocate|Free)"),
      ], [
        re.compile(".*!agent::asan::StackCaptureCache::(GetStackCapture|SaveStackTrace)"),
      ], [
        re.compile(".*!agent::asan::WindowsHeapAdapter::Heap(Re)?Alloc"),
      ], [
        re.compile(".*!asan_Heap(Re)?Alloc"),
      ],
    ],
  ),
];