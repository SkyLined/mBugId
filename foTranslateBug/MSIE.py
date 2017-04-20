from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Breakpoint -> OOM
for asBreakpoint_OOM_Stack in [
  [
    "KERNELBASE.dll!DebugBreak",
    "jscript9.dll!ReportFatalException",
    "jscript9.dll!JavascriptDispatch_OOM_fatal_error",
  ],
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "Breakpoint",
    asOriginalStackTopFrameAddresses = asBreakpoint_OOM_Stack,
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a breakpoint to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = None,
  ));
