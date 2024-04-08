from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!_?CxxThrowException",
      rb".*!abort",
    ],
  ),
  # Breakpoint -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Breakpoint",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!malloc",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a breakpoint exception to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # C++:std::bad_alloc -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"C\+\+:std::bad_alloc",
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a C++ std::bad_alloc exception to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = None,
  ),
  # AppExit -> PureCall
  cBugTranslation(
    srzOriginalBugTypeId = r"AppExit",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!_?purecall",
    ],
    s0zTranslatedBugTypeId = "PureCall",
    s0zTranslatedBugDescription = "Pure virtual function call (R6025).",
    s0zTranslatedSecurityImpact = "This is a potentially exploitable security issue",
  ),
  # PureCall -> hide irrelevant frames
  cBugTranslation(
    srzOriginalBugTypeId = r"PureCall",
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!_?purecall",
    ],
  ),
  # StackExhaustion (hide irrelevant frames)
  cBugTranslation(
    srzOriginalBugTypeId = r"StackExhaustion",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!__?chkstk",
    ],
  ),
  # hide irrelevant heap management frames
  cBugTranslation(
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!(m|re)alloc",
      rb".*!mem(chr|cmp|cpy|move|set)",
      rb".*!(.+::)?operator (delete|new(\[\])?)",
      rb".*!__scrt_throw_std_bad_alloc",
      rb".*!str(n?cat|r?chr|n?cmp|n?cpy|len|str)",
      rb".*!std::_.*",
      rb".*!std::allocator<.+>::.*",
      rb".*!std::basic_string<.+>::.*",
      rb".*!std::vector<.+>::.*",
    ],
  ),
];
