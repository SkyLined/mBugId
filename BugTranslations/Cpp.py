from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # C++ -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "C++",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!RaiseException",
      ], [
        "*!_CxxThrowException",
      ],
    ],
  ),
  # C++:std::bad_alloc -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "C++:std::bad_alloc",
    asOriginalTopStackFrameSymbols = [],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!RaiseException",
      ], [
        "*!_CxxThrowException",
      ], [
        "*!__scrt_throw_std_bad_alloc",
      ], [
        "*!malloc",
      ], [
        "*!operator new",
      ], [
        "*!operator new[]",
      ], [
        "*!std::_Allocate",
      ], [
        "*!std::allocator<...>::allocate",
      ], [
        "*!std::_Wrap_alloc<...>::allocate",
      ], [
        "*!std::_Tree_comp_alloc<...>::_Buyheadnode",
      ], [
        "*!std::_Tree_comp_alloc<...>::_Construct",
      ], [
        "*!std::_Tree_comp_alloc<..>::{ctor}",
      ], [
        "*!std::vector<...>::_Reallocate",
      ], [
        "*!std::vector<...>::_Reserve",
      ], [
        "*!std::vector<...>::resize",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a C++ std::bad_alloc exception to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # AppExit -> PureCall
  cBugTranslation(
    sOriginalBugTypeId = "AppExit",
    aasOriginalTopStackFrameSymbols = [
      [
        "*!abort",
        "*!_purecall",
      ], [
        "*!abort",
        "*!purecall",
      ],
    ],
    sTranslatedBugTypeId = "PureCall",
    sTranslatedBugDescription = "Pure virtual function call (R6025).",
    sTranslatedSecurityImpact = "This is a potentially exploitable security issue",
  ),
  # StackExhaustion (hide irrelevant frames)
  cBugTranslation(
    sOriginalBugTypeId = "StackExhaustion",
    asOriginalTopStackFrameSymbols = [
      "*!__chkstk",
    ],
  ),
];
