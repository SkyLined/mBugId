from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # ASan build related -> Ignored
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!`anonymous namespace'::Create", # Part of skia
      rb".*!base::debug::BreakDebugger",
      rb".*!base::debug::CollectGDIUsageAndDie",
      rb".*!blink::ReportFatalErrorInMainThread",
      rb".*!blink::V8ScriptRunner::CallExtraOrCrash(<.+>)?",
      rb".*!crash_reporter::internal::CrashForExceptionInNonABICompliantCodeRange",
      rb".*!CrashForException_ExportThunk",
      rb".*!crashpad::`anonymous namespace'::UnhandledExceptionHandler",
      rb".*!crashpad::CrashpadClient::DumpAndCrash",
      rb".*!raise",
      rb".*!sk_abort_no_print",
      rb".*!SkMallocPixelRef::MakeUsing",
      rb".*!v8::Utils::ApiCheck",
      rb".*!WTF::Deque<.+>::ExpandCapacity(IfNeeded)",
      rb".*!WTF::Deque<.+>::push_back",
    ],
  ),
  # Breakpoint -> Ignored
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!__sanitizer_cov",
    ],
    s0zTranslatedBugTypeId = None, # This is apparently triggered by ASAN builds to determine EIP/RIP.
    s0zTranslatedBugDescription = None,
    s0zTranslatedSecurityImpact = None,
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!base::`anonymous namespace'::OnNoMemory",
      rb".*!base::internal::SchedulerWorkerPoolImpl::Start", # CHECK() on thread start
      rb".*!base::PartitionRecommitSystemPages",
      rb".*!blink::MemoryRegion::Commit",
      rb".*!content::`anonymous namespace'::CrashOnMapFailure",
      rb".*!skia::CreateHBitmap",
      rb".*!ui::ClientGpuMemoryBufferManager::ClientGpuMemoryBufferManager", # std::vector throws breakpoint
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # Breakpoint -> Assert
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!blink::reportFatalErrorInMainThread",
      rb".*!v8::Utils::ReportApiFailure",
      rb".*!logging::LogMessage::~LogMessage",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered an exception to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = None,
  ),
  # AVW@NULL -> Assert
  cBugTranslation(
    srzOriginalBugTypeId = r"AVW@NULL",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!base::win::`anonymous namespace'::ForceCrashOnSigAbort",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered a NULL pointer access violation to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = None,
  ),
  # Various -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"0xE0000008|Assert|AVW@NULL", # 0xE0000008 (win::kOomExceptionCode) -> OOM
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!base::`anonymous namespace'::OnNoMemory",
      rb".*!(?:base|WTF)::[Pp]artitions?(?:ExcessiveAllocationSize|OutOfMemory(Using\w+)?)",
      rb".*!blink::(?:BlinkGCOutOfMemory|ReportOOMErrorInMainThread)",
      rb".*!FX_OutOfMemoryTerminate",
      rb".*!SkBitmap::allocPixels",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application caused an access violation by writing to NULL to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # OOM -> hide irrelevant frames
  cBugTranslation(
    srzOriginalBugTypeId = r"OOM",
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".+!(.+::)?(Win)?CallNewHandler",
      rb".+!(.+::)?\w+_malloc(_\w+)?",
      rb".+!(.+::)?\w*(Alloc|alloc|OutOfMemory)\w*(<.+>)?",
    ],
  ),
];
