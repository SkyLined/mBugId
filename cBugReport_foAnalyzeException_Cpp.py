import re;

def cBugReport_foAnalyzeException_Cpp(oBugReport, oCdbWrapper, oException):
  # Attempt to get the symbol of the virtual function table of the object that was thrown and add that the the type id:
  assert len(oException.auParameters) >= 3, \
      "Expected a C++ Exception to have at least 3 parameters, got %d" % len(oException.auParameters);
  poException = oException.auParameters[1];
  asExceptionVFtablePointer = oCdbWrapper.fasSendCommandAndReadOutput(
    "dps 0x%X L1; $$ Get C++ exception vftable pointer" % poException,
    bOutputIsInformative = True,
  );
  if not oCdbWrapper.bCdbRunning: return None;
  sCarriedLine = "";
  for sLine in asExceptionVFtablePointer:
    oExceptionVFtablePointerMatch = re.match(r"^[0-9A-F`]+\s*[0-9A-F`\?]+(?:\s+(.+))?\s*$", asExceptionVFtablePointer[0], re.I);
    assert oExceptionVFtablePointerMatch, "Unexpected dps result:\r\n%s" % "\r\n".join(asExceptionVFtablePointer);
    sExceptionObjectVFTablePointerSymbol = oExceptionVFtablePointerMatch.group(1);
    if sExceptionObjectVFTablePointerSymbol is None: break;
    sExceptionObjectSymbol = sExceptionObjectVFTablePointerSymbol.rstrip("::`vftable'");
    if "!" not in sExceptionObjectSymbol:
      break;
    sModuleCdbId, sExceptionClassName = sExceptionObjectSymbol.split("!", 1);
    oBugReport.sBugTypeId += ":%s" % sExceptionClassName;
    break;
  return oBugReport;
