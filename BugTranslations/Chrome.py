import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> Ignored
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "*!__sanitizer_cov",
    ],
    sTranslatedBugTypeId = None, # This is apparently triggered by ASAN builds to determine EIP/RIP.
    sTranslatedBugDescription = None,
    sTranslatedSecurityImpact = None,
  ),
  # Breakpoint (hide irrelevant frames only)
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!base::debug::BreakDebugger",
      ],
    ],
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!base::`anonymous namespace'::OnNoMemory",
      ], [
        "*!base::`anonymous namespace'::OnNoMemory",
      ], [
        "*!base::debug::CollectGDIUsageAndDie",
        "*!skia::CreateHBitmap",
      ], [
        "*!base::PartitionRecommitSystemPages",
      ], [
        "*!blink::MemoryRegion::Commit",
      ], [
        "*!content::`anonymous namespace'::CrashOnMapFailure",
      ], [
        "*!logging::LogMessage::~LogMessage",
        "*!base::`anonymous namespace'::OnNoMemory",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!`anonymous namespace'::Create", # Part of skia
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # Breakpoint -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "*!blink::reportFatalErrorInMainThread",
      "*!v8::Utils::ReportApiFailure",
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = None,
  ),
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "*!logging::LogMessage::~LogMessage",
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = None,
  ),
  # AVW@NULL -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "AVW@NULL",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!base::win::`anonymous namespace'::ForceCrashOnSigAbort",
      ],
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a NULL pointer access violation to indicate an assertion failed.",
    sTranslatedSecurityImpact = None,
  ),
  # Assert -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!abort",
      ], [
        "*!`anonymous namespace'::Create", # Part of skia
      ], [
        "*!blink::ReportFatalErrorInMainThread",
      ], [
        "*!blink::V8ScriptRunner::CallExtraOrCrash",
      ], [
        "*!blink::V8ScriptRunner::CallExtraOrCrash<2>",
      ], [
        "*!raise",
      ], [
        "*!sk_abort_no_print",
      ], [
        "*!v8::Utils::ApiCheck",
      ],
    ],
  ),
  # Assert -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Assert",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!SkBitmap::allocPixels",
      ], [
        "*!FX_OutOfMemoryTerminate",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application caused an access violation by writing to NULL to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # AVW@NULL -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "AVW@NULL",
    aasOriginalTopStackFrameSymbols = [
      [
        re.compile("^.+!(base|WTF)::[Pp]artitions?OutOfMemory(Using\w+)?$"),
      ], [
        "*!WTF::partitionExcessiveAllocationSize",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application caused an access violation by writing to NULL to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # 0xE0000008 (win::kOomExceptionCode) -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "0xE0000008",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!base::`anonymous namespace'::OnNoMemory",
      ], [
        re.compile("^.+!(base|WTF)::[Pp]artitions?OutOfMemory(Using\w+)?$"),
      ], [
        "*!blink::BlinkGCOutOfMemory",
      ], [
        "*!blink::ReportOOMErrorInMainThread",
      ], [
        "*!WTF::partitionExcessiveAllocationSize",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application caused an access violation by writing to NULL to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # OOM -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile("^.+!(.+::)?(%s)$" % "|".join([
          "(Win)?CallNewHandler",
          "\w+_malloc(_\w+)?",
          "operator new",
          "\w*(Alloc|Calloc|Malloc|Realloc|OutOfMemory)\w*(<\.\.\.>)?",
        ])),
      ], [
        "*!SkMallocPixelRef::MakeUsing",
      ], [
        "*!WTF::Deque<blink...>::ExpandCapacity",
      ], [
        "*!WTF::Deque<blink...>::ExpandCapacityIfNeeded",
      ], [
        "*!WTF::Deque<blink...>::push_back",
      ],
    ],
  ),
];
