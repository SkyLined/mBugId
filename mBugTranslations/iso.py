import re;
from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Assert -> OOM
  cBugTranslation(
    srzOriginalBugTypeId = r"Assert(:HRESULT)?",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!CIsoMalloc::_InitializeEntry",
    ],
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!CIsoScope::_?Alloc\w+",
      rb".*!IsoAllocMessageBuffer",
    ],
    s0zTranslatedBugTypeId = "OOM",
    s0zTranslatedBugDescription = "The application triggered a fail fast application exit to indicate it was unable to allocate enough memory.",
    s0zTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
];
