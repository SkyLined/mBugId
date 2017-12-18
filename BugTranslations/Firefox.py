import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> hide irrelevent stack frames
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "mozglue.dll!moz_abort",
      ], [
        # This may look to be OOM specific, but the compiler can optimize similar functions with different names to
        # use the same code, so this symbol may be returned when the source called a different function.
        "mozglue.dll!mozalloc_abort",
      ], [
        "xul.dll!Abort",
      ]
    ],
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "mozglue.dll!arena_run_split",
      ], [
        "mozglue.dll!mozalloc_handle_oom",
      ], [
        "mozglue.dll!pages_commit",
      ], [
        "xul.dll!js::CrashAtUnhandlableOOM",
      ], [
        "xul.dll!js::AutoEnterOOMUnsafeRegion::crash",
      ], [
        "xul.dll!NS_ABORT_OOM",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # IllegalInstruction -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "IllegalInstruction",
    asOriginalTopStackFrameSymbols = [
      "xul.dll!alloc::oom::default_oom_handler",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # OOM -> hide irrelevant stack frames
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile("^(mozglue|xul)\.dll!arena_\w+$"),
      ], [
        re.compile("^(mozglue|xul)\.dll!(\w+::)*\w+alloc(<\.\.\.>)?$"),
      ], [
        "xul.dll!alloc::oom::imp::oom",
      ], [
        "xul.dll!alloc::oom::oom",
      ], [
        "xul.dll!alloc::raw_vec::RawVec<...>::reserve",
      ], [
        "xul.dll!collections::vec::Vec<...>::reserve<...>",
      ],
    ],
  ),
  # Breakpoint -> Assert
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "xul.dll!NS_DebugBreak",
    ],
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
];
