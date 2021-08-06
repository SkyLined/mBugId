from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"chakra\.dll!ReportFatalException",
      rb"chakra\.dll!Js::Exception::RaiseIfScriptActive",
      rb"chakra\.dll!Js::JavascriptError::ThrowOutOfMemoryError",
      rb"chakra\.dll!Js::Throw::OutOfMemory",
      rb"chakra\.dll!Memory::HeapAllocator::Alloc",
    ],
  ),
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"chakra\.dll!Js::Throw::FatalInternalError",
    ],
    s0zTranslatedBugTypeId = "Assert",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate a fatal error was detected.",
    s0zTranslatedSecurityImpact = None,
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"chakra\.dll!MarkStack_OOM_fatal_error",
      rb"chakra\.dll!JavascriptDispatch_OOM_fatal_error",
      rb"chakra\.dll!OutOfMemory_fatal_error",
      rb"chakra\.dll!Js::JavascriptError::ThrowOutOfMemoryError",
      rb"chakra\.dll!Js::JavascriptExceptionOperators::ThrowOutOfMemory",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
];
