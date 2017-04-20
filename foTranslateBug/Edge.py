from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Breakpoint -> OOM
for asBreakpoint_OOM_Stack in [
  [
    "chakra.dll!ReportFatalException",
    "chakra.dll!MarkStack_OOM_fatal_error",
  ], [
    "KERNELBASE.dll!RaiseException",
    "EDGEHTML.dll!Abandonment::InduceAbandonment",
    "EDGEHTML.dll!Abandonment::OutOfMemory",
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalStackTopFrameAddresses = asBreakpoint_OOM_Stack,
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ));
# Breakpoint -> Assert
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalStackTopFrameAddresses = [
    "KERNELBASE.dll!RaiseException",
    "EDGEHTML.dll!Abandonment::InduceAbandonment",
    "EDGEHTML.dll!Abandonment::UnreachableCode",
  ],
  sTranslatedBugTypeId = "Assert:Unreachable",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate a supposedly unreachable code path was taken.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalStackTopFrameAddresses = [
    "KERNELBASE.dll!RaiseException",
    "EDGEHTML.dll!Abandonment::InduceAbandonment",
    "EDGEHTML.dll!Abandonment::Fail",
  ],
  sTranslatedBugTypeId = "Assert:Fail",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalStackTopFrameAddresses = [
    "KERNELBASE.dll!RaiseException",
    "EDGEHTML.dll!Abandonment::InduceAbandonment",
    "EDGEHTML.dll!Abandonment::InduceHRESULTAbandonment",
    "EDGEHTML.dll!Abandonment::CheckHRESULTStrict",
  ],
  sTranslatedBugTypeId = "Assert:HRESULT",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalStackTopFrameAddresses = [
    "KERNELBASE.dll!RaiseException",
    "EDGEHTML.dll!Abandonment::InduceAbandonment",
  ],
  sTranslatedBugTypeId = "Assert",
  sTranslatedBugDescription = "The application triggered a breakpoint to indicate an assertion failed.",
  sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
));
# FailFast -> OOM
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "FailFast",
  asOriginalStackTopFrameAddresses = [
    "EDGEHTML.dll!Abandonment::OutOfMemory",
  ],
  sTranslatedBugTypeId = "OOM",
  sTranslatedBugDescription = "The application triggered a Fail Fast exception to indicate it was unable to allocate enough memory.",
  sTranslatedSecurityImpact = None,
));
for asFailFast_Assert_Stack in [
  [
    "EDGEHTML.dll!Abandonment::CheckHRESULT",
  ], [
    "EDGEHTML.dll!Abandonment::CheckHRESULTStrict",
  ], [
    "EDGEHTML.dll!Abandonment::InvalidArguments",
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalStackTopFrameAddresses = asFailFast_Assert_Stack,
    sTranslatedBugTypeId = "Assert",
    sTranslatedBugDescription = "The application triggered a Fail Fast exception to indicate an assertion failed.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ));
