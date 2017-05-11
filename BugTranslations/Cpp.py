import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # C++ -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "C++",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!RaiseException",
      ], [
        re.compile("^.*!_CxxThrowException$"),
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
        re.compile("^.*!_CxxThrowException$"),
      ], [
        re.compile("^.*!__scrt_throw_std_bad_alloc$"),
      ], [
        re.compile("^.*!malloc$"),
      ], [
        re.compile("^.*!operator new$"),
      ], [
        re.compile("^.*!std::_Allocate$"),
      ], [
        re.compile("^.*!std::allocator<\.\.\.>::allocate$"),
      ], [
        re.compile("^.*!std::_Wrap_alloc<\.\.\.>::allocate$"),
      ], [
        re.compile("^.*!std::_Tree_comp_alloc<\.\.\.>::_Buyheadnode$"),
      ], [
        re.compile("^.*!std::_Tree_comp_alloc<\.\.\.>::_Construct$"),
      ], [
        re.compile("^.*!std::_Tree_comp_alloc<\.\.\.>::{ctor}$"),
      ], [
        re.compile("^.*!std::vector<...>::_Reallocate$"),
      ], [
        re.compile("^.*!std::vector<...>::_Reserve$"),
      ], [
        re.compile("^.*!std::vector<...>::resize$"),
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
