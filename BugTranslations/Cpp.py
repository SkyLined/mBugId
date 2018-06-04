import re;
from .cBugTranslation import cBugTranslation;
from .rHeapRelatedBugIds import rHeapRelatedBugIds;

aoBugTranslations = [
  # C++ -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = re.compile(r"C\+\+(\:.+)?"),
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!RaiseException",
      ], [
        re.compile(r".*!_?CxxThrowException"),
      ],
    ],
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalTopStackFrameSymbols = [
      "*!malloc",
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered abreakpoint exception to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # C++:std::bad_alloc -> OOM
  cBugTranslation(
    sOriginalBugTypeId = "C++:std::bad_alloc",
    asOriginalTopStackFrameSymbols = [],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a C++ std::bad_alloc exception to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ),
  # AppExit -> PureCall
  cBugTranslation(
    sOriginalBugTypeId = "AppExit",
    asOriginalTopStackFrameSymbols = [
      "*!abort",
      re.compile(r".*!_?purecall"),
    ],
    sTranslatedBugTypeId = "PureCall",
    sTranslatedBugDescription = "Pure virtual function call (R6025).",
    sTranslatedSecurityImpact = "This is a potentially exploitable security issue",
  ),
  # PureCall -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "PureCall",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile(r".*!_?purecall"),
      ],
    ],
  ),
  # StackExhaustion (hide irrelevant frames)
  cBugTranslation(
    sOriginalBugTypeId = "StackExhaustion",
    asOriginalTopStackFrameSymbols = [
      "*!__chkstk",
    ],
  ),
  # Heap related issues -> hide irrelevant heap management frames
  cBugTranslation(
    sOriginalBugTypeId = rHeapRelatedBugIds,
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile(r".*!(m|re)alloc"),
      ], [
        re.compile(r".*!mem(chr|cmp|cpy|move|set)"),
      ], [
        re.compile(r".*!operator (delete|new(\[\])?)"),
      ], [
        "*!__scrt_throw_std_bad_alloc",
      ], [
        re.compile(r".*!str(n?cat|r?chr|n?cmp|n?cpy|len|str)"),
      ], [
        "*!std::_Allocate",
      ], [
        "*!std::allocator<...>::allocate",
      ], [
        re.compile(r".*!std::basic_string<...>::(_Construct_lv_contents|_Copy|_Grow|assign|basic_string<...>)"),
      ], [
        re.compile(r".*!std::_Tree_comp_alloc<...>::(_Buyheadnode|_Construct|\{ctor\})"),
      ], [
        re.compile(r".*!std::vector<...>::(_Reallocate|_Reserve|resize)"),
      ], [
        "*!std::_Wrap_alloc<...>::allocate",
      ], [
        "*!std::_Xbad_alloc",
      ],
    ],
  ),
];
