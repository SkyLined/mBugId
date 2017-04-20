from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# C++ -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "C++:std::bad_alloc",
  asOriginalStackTopFrameAddresses = [
    "kernelbase.dll!RaiseException",
    "*!_CxxThrowException",
    "*!__scrt_throw_std_bad_alloc",
    "*!operator new",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a C++ std::bad_alloc exception to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "C++:std::bad_alloc",
  asOriginalStackTopFrameAddresses = [
    "kernelbase.dll!RaiseException",
    "*!_CxxThrowException",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a C++ std::bad_alloc exception to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));

for asAppExit_PureCall_Stack in [
  [
    "*!abort",
    "*!_purecall",
  ], [
    "*!abort",
    "*!purecall",
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "AppExit",
    asOriginalStackTopFrameAddresses = asAppExit_PureCall_Stack,
    sTranslatedBugTypeId = "PureCall",
    sTranslatedBugDescription = "Pure virtual function call (R6025).",
    sTranslatedSecurityImpact = "This is a potentially exploitable security issue",
  ));
