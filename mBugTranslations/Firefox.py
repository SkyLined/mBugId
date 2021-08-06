import re;
from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> hide irrelevent stack frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"(mozglue|xul)\.dll!Abort",
      rb"(mozglue|xul)\.dll!arena_\w+",
      rb"(mozglue|xul)\.dll!(.*::)?\w+alloc(<.+>|::.*)?",
      rb"(mozglue|xul)\.dll!collections::vec::Vec<.+>::reserve<.+>",
      rb"(mozglue|xul)\.dll!moz_abort",
      rb"(mozglue|xul)\.dll!mozalloc_abort",
    ],
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"mozglue\.dll!arena_run_split",
      rb"mozglue\.dll!mozalloc_handle_oom",
      rb"mozglue\.dll!pages_commit",
      rb"xul\.dll!js::CrashAtUnhandlableOOM",
      rb"xul\.dll!js::AutoEnterOOMUnsafeRegion::crash",
      rb"xul\.dll!NS_ABORT_OOM",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # IllegalInstruction -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"IllegalInstruction",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"xul\.dll!alloc::oom::default_oom_handler",
      rb"xul\.dll!alloc::heap::\{\{impl\}\}::oom",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # Breakpoint -> Assert
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"xul\.dll!NS_DebugBreak",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
];
