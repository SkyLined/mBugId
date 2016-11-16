# Some breakpoints may indicate an out-of-memory bug, heap corruption, or no bug at all:
dtxBugTranslations = {
  "OOM": (
    "A breakpoint was triggered because the program was unable to allocate enough memory",
    None,
    [
      [     # Chrome
        "chrome.dll!base::`anonymous namespace'::OnNoMemory",
      ], [
        "chrome_child.dll!base::`anonymous namespace'::OnNoMemory",
      ], [
        "chrome.dll!base::debug::BreakDebugger",
        "chrome.dll!logging::LogMessage::~LogMessage",
        "chrome.dll!base::`anonymous namespace'::OnNoMemory",
      ], [
        "chrome_child.dll!base::debug::BreakDebugger",
        "chrome_child.dll!logging::LogMessage::~LogMessage",
        "chrome_child.dll!base::`anonymous namespace'::OnNoMemory",
      ], [
        "chrome_child.dll!base::debug::BreakDebugger",
        "chrome_child.dll!content::`anonymous namespace'::CrashOnMapFailure",
      ], [
        "chrome_child.dll!blink::reportFatalErrorInMainThread",
        "chrome_child.dll!v8::Utils::ReportApiFailure",
        "chrome_child.dll!v8::Utils::ApiCheck",
        "chrome_child.dll!v8::internal::V8::FatalProcessOutOfMemory",
      ], [  # Edge
        "KERNELBASE.dll!RaiseException",
        "EDGEHTML.dll!Abandonment::InduceAbandonment",
        "EDGEHTML.dll!Abandonment::OutOfMemory",
      ], [
        "chakra.dll!ReportFatalException",
        "chakra.dll!MarkStack_OOM_fatal_error",
      ], [  # Firefox
        "mozglue.dll!mozalloc_abort",
        "mozglue.dll!mozalloc_handle_oom",
      ], [
        "mozglue.dll!moz_abort",
        "mozglue.dll!pages_commit",
      ], [
        "mozglue.dll!moz_abort",
        "mozglue.dll!arena_run_split",
        "mozglue.dll!arena_malloc_large",
        "mozglue.dll!je_malloc",
      ], [
        "xul.dll!js::CrashAtUnhandlableOOM",
      ], [
        "xul.dll!js::AutoEnterOOMUnsafeRegion::crash",
      ], [
        "xul.dll!NS_ABORT_OOM",
      ], [  # MSIE
        "KERNELBASE.dll!DebugBreak",
        "jscript9.dll!ReportFatalException",
        "jscript9.dll!JavascriptDispatch_OOM_fatal_error",
      ],
    ],
  ),
  "HeapCorrupt": (
    "A breakpoint was triggered because a corrupted heap block was detected",
    "This is probably an exploitable security issue",
    [
      [
        # This should now be covered by cCdbWrapper_fbDetectAndReportVerifierErrors, but just in case something slips
        # through, we'll leave this in:
        "verifier.dll!VerifierStopMessage",
        "verifier.dll!AVrfpDphReportCorruptedBlock",
      ],
      [
        "ntdll.dll!RtlReportCriticalFailure",
        "ntdll.dll!RtlpHeapHandleError",
      ],
      [
        "ntdll.dll!RtlpBreakPointHeap",
      ],
    ],
  ),
  "Assert": (
    "A breakpoint was triggered because an assertion failed",
    None,
    [
      [  # Edge
        "KERNELBASE.dll!RaiseException",
        "EDGEHTML.dll!Abandonment::InduceAbandonment",
        "EDGEHTML.dll!Abandonment::UnreachableCode", # Same as below, but with additional function hidden.
      ], [
        "KERNELBASE.dll!RaiseException",
        "edgehtml.dll!Abandonment::InduceAbandonment",
        None, # Stack walking fails here
        "edgehtml.dll!Abandonment::Fail",
      ], [
        "KERNELBASE.dll!RaiseException",
        "edgehtml.dll!Abandonment::InduceAbandonment",
      ], [ # Firefox
        "mozglue.dll!mozalloc_abort",
        "xul.dll!Abort",
        "xul.dll!NS_DebugBreak",
      ],
    ],
  ),
  None: (
    None,
    None,
    [
      [ # Chrome Asan builds trigger a breakpoint in __sanitizer_cov, apparently to determine the return address.
        "chrome.dll!__sanitizer_cov",
      ],
      [
        "chrome_elf.dll!__sanitizer_cov",
      ],
      [
        "chrome_child.dll!__sanitizer_cov",
      ],
    ],
  ),
};

def cBugReport_foAnalyzeException_STATUS_BREAKPOINT(oBugReport, oCdbWrapper, oException):
  oBugReport = oBugReport.foTranslate(dtxBugTranslations);
  return oBugReport;
