import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# AVE@NULL -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "AVE@NULL",
  asOriginalTopStackFrameSymbols = [
    "0x0",
    "*!v8::base::OS::Abort",
    "*!v8::Utils::ReportApiFailure",
    "*!v8::Utils::ApiCheck",
    "*!v8::internal::V8::FatalProcessOutOfMemory",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application caused an access violation by calling NULL to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
# AVW@NULL -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "AVW@NULL",
  aasOriginalTopStackFrameSymbols = [
    [
      "*!WTF::partitionOutOfMemory",
    ], [
      "*!WTF::partitionsOutOfMemoryUsingLessThan16M",
    ], [
      "*!WTF::partitionsOutOfMemoryUsing16M",
    ], [
      "*!WTF::partitionsOutOfMemoryUsing32M",
    ], [
      "*!WTF::partitionsOutOfMemoryUsing64M",
    ], [
      "*!WTF::partitionsOutOfMemoryUsing128M",
    ], [
      "*!WTF::partitionsOutOfMemoryUsing256M",
    ], [
      "*!WTF::partitionsOutOfMemoryUsing512M",
    ], [
      "*!WTF::partitionExcessiveAllocationSize",
    ], [
      "*!base::win::`anonymous namespace'::ForceCrashOnSigAbort",
      "*!raise",
      "*!abort",
      "*!sk_abort_no_print",
      "*!SkBitmap::allocPixels",
    ], [
      "*!base::win::`anonymous namespace'::ForceCrashOnSigAbort",
      "*!raise",
      "*!abort",
      "*!sk_abort_no_print",
      "*!SkBitmap::allocPixels",
    ],
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application caused an access violation by writing to NULL to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "OOM",
  aasOriginalTopStackFrameSymbols = [
    [
      "*!SkBitmap::allocPixels",
    ], [
      "*!SkBitmap::allocN32Pixels",
    ], [
      "*!SkBitmap::allocPixels",
    ], [
      "*!SkBitmap::allocN32Pixels",
    ],
  ],
));
# Breakpoint (hide irrelevant frames only)
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalTopStackFrameSymbols = [
    "*!base::debug::BreakDebugger",
  ],
));

# Breakpoint -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  aasOriginalTopStackFrameSymbols = [
    [
      "*!base::`anonymous namespace'::OnNoMemory",
    ], [
      "*!base::`anonymous namespace'::OnNoMemory",
    ], [
      "*!logging::LogMessage::~LogMessage",
      "*!base::`anonymous namespace'::OnNoMemory",
    ], [
      "*!logging::LogMessage::~LogMessage",
      "*!base::`anonymous namespace'::OnNoMemory",
    ], [
      "*!content::`anonymous namespace'::CrashOnMapFailure",
    ], [
      "*!base::debug::CollectGDIUsageAndDie",
      "*!skia::CreateHBitmap",
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
));
# Breakpoint -> Assert
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalTopStackFrameSymbols = [
    "*!blink::reportFatalErrorInMainThread",
    "*!v8::Utils::ReportApiFailure",
  ],
  aasAdditionalIrrelevantStackFrameSymbols = [
    [
      "*!v8::Utils::ApiCheck",
    ], [
      "*!`anonymous namespace'::Create", # Part of skia
    ],
  ],
  sTranslatedBugTypeId = "Assert",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = None,
));
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalTopStackFrameSymbols = [
    "*!logging::LogMessage::~LogMessage",
  ],
  sTranslatedBugTypeId = "Assert",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = None,
));
# Assert -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Assert",
  asOriginalTopStackFrameSymbols = [
    "*!v8::internal::V8::FatalProcessOutOfMemory",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));

# Breakpoint -> Ignored
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalTopStackFrameSymbols = [
    "*!__sanitizer_cov",
  ],
  sTranslatedBugTypeId = None, # This is apparently triggered by ASAN builds to determine EIP/RIP.
  sTranslatedBugDescription = None,
  sTranslatedSecurityImpact = None,
));

# OOM -> OOM (hide irrelevant frames)
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "OOM",
  aasAdditionalIrrelevantStackFrameSymbols = [
    [
      "*!base::allocator::WinHeapMalloc",
    ], [
      "*!`anonymous namespace'::DefaultWinHeapMallocImpl",
    ], [
      "*!ShimMalloc",
    ],
  ],
));