# Hide some functions at the top of the stack that are merely helper functions and not relevant to the bug:
asHiddenTopFrames = [
  # Functions that are used to trigger the exception, but are not the source of the bug:
  "KERNELBASE.dll!RaiseException",
  "iertutil.dll!ATL::AtlThrowImpl",
];
def cBugReport_foAnalyzeException_STATUS_NO_MEMORY(oBugReport, oCdbWrapper, oException):
  oBugReport.oStack.fHideTopFrames(asHiddenTopFrames);
  oBugReport.sBugDescription = "An exception was raised because the program was unable to allocate enough memory",
  return oBugReport;
