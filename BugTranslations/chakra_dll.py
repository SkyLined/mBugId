from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Breakpoint -> hide irrelevant frames
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "chakra.dll!ReportFatalException",
      ],
    ],
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    aasOriginalTopStackFrameSymbols = [
      [
        "chakra.dll!MarkStack_OOM_fatal_error",
      ], [
        "chakra.dll!JavascriptDispatch_OOM_fatal_error",
      ], [
        "chakra.dll!OutOfMemory_fatal_error",
      ], [
        "chakra.dll!Js::JavascriptError::ThrowOutOfMemoryError",
      ], [
        "chakra.dll!Js::JavascriptExceptionOperators::ThrowOutOfMemory",
      ],
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "chakra.dll!Js::Exception::RaiseIfScriptActive",
      ], [
        "chakra.dll!Js::JavascriptError::ThrowOutOfMemoryError",
      ], [
        "chakra.dll!Js::Throw::OutOfMemory",
      ], [
        "chakra.dll!Memory::HeapAllocator::Alloc",
      ]
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
];
