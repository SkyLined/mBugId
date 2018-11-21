from .dxConfig import dxConfig;

# Source: winnt.h (codemachine.com/downloads/win81/winnt.h)
# I couldn't find much information on most of these exceptions, so this may be incorrect or at least incomplete.
dtsFastFailErrorInformation_by_uCode = {
  0:  ("OOBW:Stack",    "/GS detected that a stack cookie was modified",              "Potentially exploitable security issue"),
  1:  ("VTGuard",       "VTGuard detected an invalid virtual function table cookie",  "Potentially exploitable security issue"),
  2:  ("OOBW:Stack",    "/GS detected that a stack cookie was modified",              "Potentially exploitable security issue"),
  3:  ("CorruptList",   "Safe unlinking detected a corrupted LIST_ENTRY",             "Potentially exploitable security issue"),
  4:  ("BadStack",      "FAST_FAIL_INCORRECT_STACK",                                  "Potentially exploitable security issue"),
  5:  ("InvalidArg",    "FAST_FAIL_INVALID_ARG",                                      "Potentially exploitable security issue"),
  6:  ("GSCookie",      "FAST_FAIL_GS_COOKIE_INIT",                                   "Potentially exploitable security issue"),
  # TODO: It may be possible to check if an AppExit is an R6025: this only happens on x86, the first frame should be
  # "application!abort" and the second frame should be a non-static call (e.g. CALL EAX) from the application.
  # However, I'm worried about false positives and this does not appear to happen often enough to warrant the expense
  # of creating code for it at the moment.
  7:  ("AppExit",       "Fatal application error, possibly a pure virtual function call (R6025)",
                                                                                      "Potentially exploitable security issue"),
  8:  ("RangeCheck",    "FAST_FAIL_RANGE_CHECK_FAILURE",                              "Potentially exploitable security issue"),
  9:  ("Registry",      "FAST_FAIL_UNSAFE_REGISTRY_ACCESS",                           "Potentially exploitable security issue"),
  10: ("CFG",           "Control Flow Guard detected a call to an invalid address",   "Potentially exploitable security issue"),
  11: ("GuardWrite",    "FAST_FAIL_GUARD_WRITE_CHECK_FAILURE",                        "Potentially exploitable security issue"),
  12: ("FiberSwitch",   "FAST_FAIL_INVALID_FIBER_SWITCH",                             "Potentially exploitable security issue"),
  13: ("SetContext",    "FAST_FAIL_INVALID_SET_OF_CONTEXT",                           "Potentially exploitable security issue"),
  14: ("RefCount",      "A reference counter was incremented beyond its maximum",     "Potentially exploitable security issue"),
  18: ("JumpBuffer",    "FAST_FAIL_INVALID_JUMP_BUFFER",                              "Potentially exploitable security issue"),
  19: ("MrData",        "FAST_FAIL_MRDATA_MODIFIED",                                  "Potentially exploitable security issue"),
  20: ("Cert",          "FAST_FAIL_CERTIFICATION_FAILURE",                            "Potentially exploitable security issue"),
  21: ("ExceptChain",   "FAST_FAIL_INVALID_EXCEPTION_CHAIN",                          "Potentially exploitable security issue"),
  22: ("Crypto",        "FAST_FAIL_CRYPTO_LIBRARY",                                   "Potentially exploitable security issue"),
  23: ("DllCallout",    "FAST_FAIL_INVALID_CALL_IN_DLL_CALLOUT"                       "Potentially exploitable security issue"),
  24: ("ImageBase",     "FAST_FAIL_INVALID_IMAGE_BASE",                               "Potentially exploitable security issue"),
  25: ("DLoadProt",     "FAST_FAIL_DLOAD_PROTECTION_FAILURE",                         "Potentially exploitable security issue"),
  26: ("ExtCall",       "FAST_FAIL_UNSAFE_EXTENSION_CALL",                            "Potentially exploitable security issue"),
};
auErrorCodesForWhichAStackDumpIsUseful = [
  0, #LegacyGS
  2, #StackCookie
  4, #BadStack
];

def cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN(oBugReport, oProcess, oThread, oException):
  # Parameter[0] = fail fast code
  assert len(oException.auParameters) == 1, \
      "Unexpected number of fail fast exception parameters (%d vs 1)" % len(oException.auParameters);
  uFastFailCode = oException.auParameters[0];
  sFastFailCodeId, sFastFailCodeDescription, sSecurityImpact = dtsFastFailErrorInformation_by_uCode.get( \
      uFastFailCode, ("Unknown", "unknown code", "May be a security issue"));
  oBugReport.sBugTypeId = sFastFailCodeId;
  if sFastFailCodeDescription.startswith("FAST_FAIL_"):
    oBugReport.sBugDescription = "A critical issue was detected (code %X, fail fast code %d: %s)" % \
        (oException.uCode, uFastFailCode, sFastFailCodeDescription);
  else:
    oBugReport.sBugDescription = sFastFailCodeDescription;
  oBugReport.sSecurityImpact = sSecurityImpact;
  if oProcess.oCdbWrapper.bGenerateReportHTML and uFastFailCode in auErrorCodesForWhichAStackDumpIsUseful:
    uStackPointer = oThread.fuGetRegister("*sp");
    # TODO: Call !teb, parse "StackLimit:", trim stack memory dump if needed.
    uSize = dxConfig["uStackDumpSizeInPointers"] * oProcess.uPointerSize;
    if uSize > dxConfig["uMaxMemoryDumpSize"]:
      uSize = dxConfig["uMaxMemoryDumpSize"];
    oBugReport.fAddMemoryDump(uStackPointer, uStackPointer + uSize, "Stack");
    oBugReport.atxMemoryRemarks.append(("Stack pointer", uStackPointer, oProcess.uPointerSize));
  return oBugReport;
