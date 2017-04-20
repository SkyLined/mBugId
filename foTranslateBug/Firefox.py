from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Breakpoint -> OOM
for asBreakpoint_OOM_Stack in [
  [
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
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalStackTopFrameAddresses = asBreakpoint_OOM_Stack,
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ));
# Breakpoint -> Assert
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalStackTopFrameAddresses = [
    "mozglue.dll!mozalloc_abort",
    "xul.dll!Abort",
    "xul.dll!NS_DebugBreak",
  ],
  sTranslatedBugTypeId = "Assert",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
