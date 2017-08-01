from fsGetCPPObjectClassNameFromVFTable import fsGetCPPObjectClassNameFromVFTable;

def cBugReport_foAnalyzeException_Cpp(oBugReport, oProcess, oException):
  # Attempt to get the symbol of the virtual function table of the object that was thrown and add that the the type id:
  assert len(oException.auParameters) >= 3, \
      "Expected a C++ Exception to have at least 3 parameters, got %d" % len(oException.auParameters);
  uCPPExceptionObjectAddress = oException.auParameters[1];
  sExceptionObjectClassName = fsGetCPPObjectClassNameFromVFTable(oProcess, uCPPExceptionObjectAddress);
  if sExceptionObjectClassName:
    oBugReport.sBugTypeId += ":%s" % sExceptionObjectClassName;
  return oBugReport;
