from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Breakpoint --> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalTopStackFrameSymbols = [
    "syzyasan_rtl.dll!base::debug::BreakDebugger",
    "syzyasan_rtl.dll!agent::asan::StackCaptureCache::AllocateCachePage",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "ASAN triggered a breakpoint to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
# OOM (hide irrelevant frames only)
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "OOM",
  aasOriginalTopStackFrameSymbols = [
    [
      "syzyasan_rtl.dll!agent::asan::StackCaptureCache::GetStackCapture",
    ], [
      "syzyasan_rtl.dll!agent::asan::StackCaptureCache::SaveStackTrace",
    ], [
      "syzyasan_rtl.dll!agent::asan::heap_managers::BlockHeapManager::Free",
    ], [
      "syzyasan_rtl.dll!agent::asan::heap_managers::BlockHeapManager::Allocate",
    ], [
      "syzyasan_rtl.dll!agent::asan::WindowsHeapAdapter::HeapAlloc",
    ], [
      "syzyasan_rtl.dll!asan_HeapAlloc",
    ],
  ],
));
