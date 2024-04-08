from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # These frames are never relevant
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"ntdll\.dll!_C_specific_handler",
      rb"ntdll\.dll!DbgBreakPoint",
      rb"ntdll\.dll!DbgPrintEx",
      rb"ntdll\.dll!DbgUiRemoteBreakin",
      rb"ntdll\.dll!FindNodeOrParent",
      rb"ntdll\.dll!KiRaiseUserExceptionDispatcher",
      rb"ntdll\.dll!KiUserExceptionDispatch",
      rb"ntdll\.dll!LdrpHandleInvalidUserCallTarget",
      rb"ntdll\.dll!RtlDeleteCriticalSection",
      rb"ntdll\.dll!RtlDispatchException",
      rb"ntdll\.dll!RtlFailFast\d*",
      rb"ntdll\.dll!RtlInsertElementGenericTableAvl",
      rb"ntdll\.dll!Rtlp?(Debug)?(Allocate|Free)Heap\w*",
      rb"ntdll\.dll!RtlpExecuteHandlerForException",
      rb"ntdll\.dll!RtlpFreeDebugInfo",
      rb"ntdll\.dll!RtlpHandleInvalidUserCallTarget",
      rb"ntdll\.dll!RtlRaiseException",
      rb"ntdll\.dll!RtlReportCriticalFailure",
      rb"ntdll\.dll!RtlUserThreadStart$filt$0",
      rb"ntdll\.dll!vDbgPrintExWithPrefixInternal",
    ],
  ),
  # Breakpoint -> HeapCorrupt
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"ntdll\.dll!RtlpHeapHandleError",
      rb"ntdll\.dll!RtlpBreakPointHeap",
    ],
    s0zTranslatedBugTypeId = "HeapCorrupt",
    s0zTranslatedBugDescription = "A breakpoint was triggered to indicate heap corruption was detected",
    s0zTranslatedSecurityImpact = "This is probably an exploitable security issue",
  ),
  # AVR@Reserved -> AVR@CFG
  cBugTranslation(
    srzOriginalBugTypeId = r"AVR@(?:Reserved|Invalid)",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"ntdll\.dll!LdrpDispatchUserCallTarget",
      rb"ntdll\.dll!LdrpValidateUserCallTarget(?:BitMapCheck|ES)?",
    ],
    s0zTranslatedBugTypeId = "AVR@CFG",
    s0zTranslatedBugDescription = "The process attempted to call a function using an invalid function pointer, " \
        "which caused an access violation exception in Control Flow Guard. This is often caused by a NULL pointer.",
    s0zTranslatedSecurityImpact = "Unlikely to be an exploitable security issue, unless you can control the invalid function pointer",
  ),
  # AVE:NULL @ ntdll.dll!NtWow64IsProcessorFeaturePresent -> ignore
  cBugTranslation(
    srzOriginalBugTypeId = r"AVE:NULL",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"ntdll\.dll!NtWow64IsProcessorFeaturePresent",
    ],
    s0zTranslatedBugTypeId = None,
  ),
  # AVW:NULL @ ntdll.dll!RtlpWaitOnCriticalSection -> ignore
  cBugTranslation(
    srzOriginalBugTypeId = r"AVW:NULL(\+.*)?",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"ntdll\.dll!RtlpWaitOnCriticalSection",
    ],
    s0zTranslatedBugTypeId = None,
  ),
];