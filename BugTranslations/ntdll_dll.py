import re;
from .cBugTranslation import cBugTranslation;
from .rHeapRelatedBugIds import rHeapRelatedBugIds;

aoBugTranslations = [
  # These frames are never relevant
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "ntdll.dll!_C_specific_handler",
      ], [
        "ntdll.dll!DbgBreakPoint",
      ], [
        "ntdll.dll!KiRaiseUserExceptionDispatcher",
      ], [
        "ntdll.dll!KiUserExceptionDispatch",
      ], [
        "ntdll.dll!RtlDispatchException",
      ], [
        "ntdll.dll!RtlpExecuteHandlerForException",
      ], [
        "ntdll.dll!RtlRaiseException",
      ], [
        "ntdll.dll!RtlUserThreadStart$filt$0",
      ],
    ],
  ),
  # Breakpoint -> HeapCorrupt
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "ntdll.dll!RtlReportCriticalFailure",
        "ntdll.dll!RtlpHeapHandleError",
      ], [
        "ntdll.dll!RtlpBreakPointHeap",
      ],
    ],
    sTranslatedBugTypeId = "HeapCorrupt",
    sTranslatedBugDescription = "A breakpoint was triggered to indicate heap corruption was detected",
    sTranslatedSecurityImpact = "This is probably an exploitable security issue",
  ),
  # AVR@Reserved -> AVR@CFG
  cBugTranslation(
    sOriginalBugTypeId = re.compile(r"^AVR@(Reserved|Invalid)$"),
    aasOriginalTopStackFrameSymbols = [
      [
        "ntdll.dll!LdrpDispatchUserCallTarget",
      ], [
        re.compile(r"ntdll\.dll!LdrpValidateUserCallTarget(BitMapCheck|ES)?"),
      ],
    ],
    sTranslatedBugTypeId = "AVR@CFG",
    sTranslatedBugDescription = "The process attempted to call a function using an invalid function pointer, " \
        "which caused an access violation exception in Control Flow Guard. This is often caused by a NULL pointer.",
    sTranslatedSecurityImpact = "Unlikely to be an exploitable security issue, unless you can control the invalid function pointer",
  ),
  # CFG -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "CFG",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "ntdll.dll!LdrpHandleInvalidUserCallTarget",
      ], [
        "ntdll.dll!RtlFailFast2",
      ], [
        "ntdll.dll!RtlpHandleInvalidUserCallTarget",
      ],
    ],
  ),
  # Heap related issues -> hide irrelevant heap management frames
  cBugTranslation(
    sOriginalBugTypeId = rHeapRelatedBugIds,
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "ntdll.dll!DbgUiRemoteBreakin",
      ], [
        "ntdll.dll!FindNodeOrParent",
      ], [
        "ntdll.dll!RtlDeleteCriticalSection",
      ], [
        "ntdll.dll!RtlInsertElementGenericTableAvl",
      ], [
        "ntdll.dll!RtlpFreeDebugInfo",
      ], [
        re.compile(r"ntdll\.dll!Rtlp?(Debug)?(Allocate|Free)Heap\w*"),
      ],
    ],
  ),
  # Debug output errors -> hide irrelevant frames
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "ntdll.dll!DbgPrintEx",
      ], [
        "ntdll.dll!vDbgPrintExWithPrefixInternal",
      ],
    ],
  ),
];