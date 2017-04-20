from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# AVE@NULL -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "AVE@NULL",
  asOriginalStackTopFrameAddresses = [
    "0x0",
    "chrome_child.dll!v8::base::OS::Abort",
    "chrome_child.dll!v8::Utils::ReportApiFailure",
    "chrome_child.dll!v8::Utils::ApiCheck",
    "chrome_child.dll!v8::internal::V8::FatalProcessOutOfMemory",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application caused an access violation by calling NULL to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
# AVW@NULL -> OOM
for asAVW_NULL_OOMStack in [
  [
    "chrome_child.dll!WTF::partitionOutOfMemory",
  ], [
    "chrome_child.dll!WTF::partitionsOutOfMemoryUsingLessThan16M",
  ], [
    "chrome_child.dll!WTF::partitionsOutOfMemoryUsing16M",
  ], [
    "chrome_child.dll!WTF::partitionsOutOfMemoryUsing32M",
  ], [
    "chrome_child.dll!WTF::partitionsOutOfMemoryUsing64M",
  ], [
    "chrome_child.dll!WTF::partitionsOutOfMemoryUsing128M",
  ], [
    "chrome_child.dll!WTF::partitionsOutOfMemoryUsing256M",
  ], [
    "chrome_child.dll!WTF::partitionsOutOfMemoryUsing512M",
  ], [
    "chrome_child.dll!WTF::partitionExcessiveAllocationSize",
  ], [
    "chrome_child.dll!base::win::`anonymous namespace'::ForceCrashOnSigAbort",
    "chrome_child.dll!raise",
    "chrome_child.dll!abort",
    "chrome_child.dll!sk_abort_no_print",
    "chrome_child.dll!SkBitmap::allocPixels",
    "chrome_child.dll!SkBitmap::allocPixels",
    "chrome_child.dll!SkBitmap::allocN32Pixels",
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "AVW@NULL",
    asOriginalStackTopFrameAddresses = asAVW_NULL_OOMStack,
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application caused an access violation by writing to NULL to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ));
# Breakpoint -> OOM
for asBreakpoint_OOM_Stack in [
  [
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
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalStackTopFrameAddresses = asBreakpoint_OOM_Stack,
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ));
# Breakpoint -> Ignored
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalStackTopFrameAddresses = [
    "*!__sanitizer_cov",
  ],
  sTranslatedBugTypeId = None, # This is apparently triggered by ASAN builds to determine EIP/RIP.
  sTranslatedBugDescription = None,
  sTranslatedSecurityImpact = None,
));
