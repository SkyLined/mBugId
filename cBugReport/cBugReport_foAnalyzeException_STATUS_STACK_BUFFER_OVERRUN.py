
from mWindowsSDK import \
    FAST_FAIL_LEGACY_GS_VIOLATION, \
    FAST_FAIL_VTGUARD_CHECK_FAILURE, \
    FAST_FAIL_STACK_COOKIE_CHECK_FAILURE, \
    FAST_FAIL_CORRUPT_LIST_ENTRY, \
    FAST_FAIL_INCORRECT_STACK, \
    FAST_FAIL_INVALID_ARG, \
    FAST_FAIL_GS_COOKIE_INIT, \
    FAST_FAIL_FATAL_APP_EXIT, \
    FAST_FAIL_RANGE_CHECK_FAILURE, \
    FAST_FAIL_UNSAFE_REGISTRY_ACCESS, \
    FAST_FAIL_GUARD_ICALL_CHECK_FAILURE, \
    FAST_FAIL_GUARD_WRITE_CHECK_FAILURE, \
    FAST_FAIL_INVALID_FIBER_SWITCH, \
    FAST_FAIL_INVALID_SET_OF_CONTEXT, \
    FAST_FAIL_INVALID_REFERENCE_COUNT, \
    FAST_FAIL_INVALID_JUMP_BUFFER, \
    FAST_FAIL_MRDATA_MODIFIED, \
    FAST_FAIL_CERTIFICATION_FAILURE, \
    FAST_FAIL_INVALID_EXCEPTION_CHAIN, \
    FAST_FAIL_CRYPTO_LIBRARY, \
    FAST_FAIL_INVALID_CALL_IN_DLL_CALLOUT, \
    FAST_FAIL_INVALID_IMAGE_BASE, \
    FAST_FAIL_DLOAD_PROTECTION_FAILURE, \
    FAST_FAIL_UNSAFE_EXTENSION_CALL, \
    FAST_FAIL_DEPRECATED_SERVICE_INVOKED, \
    FAST_FAIL_INVALID_BUFFER_ACCESS, \
    FAST_FAIL_INVALID_BALANCED_TREE, \
    FAST_FAIL_INVALID_NEXT_THREAD, \
    FAST_FAIL_GUARD_ICALL_CHECK_SUPPRESSED, \
    FAST_FAIL_APCS_DISABLED, \
    FAST_FAIL_INVALID_IDLE_STATE, \
    FAST_FAIL_MRDATA_PROTECTION_FAILURE, \
    FAST_FAIL_UNEXPECTED_HEAP_EXCEPTION, \
    FAST_FAIL_INVALID_LOCK_STATE, \
    FAST_FAIL_GUARD_JUMPTABLE, \
    FAST_FAIL_INVALID_LONGJUMP_TARGET, \
    FAST_FAIL_INVALID_DISPATCH_CONTEXT, \
    FAST_FAIL_INVALID_THREAD, \
    FAST_FAIL_INVALID_SYSCALL_NUMBER, \
    FAST_FAIL_INVALID_FILE_OPERATION, \
    FAST_FAIL_LPAC_ACCESS_DENIED, \
    FAST_FAIL_GUARD_SS_FAILURE, \
    FAST_FAIL_LOADER_CONTINUITY_FAILURE, \
    FAST_FAIL_GUARD_EXPORT_SUPPRESSION_FAILURE, \
    FAST_FAIL_INVALID_CONTROL_STACK, \
    FAST_FAIL_SET_CONTEXT_DENIED, \
    FAST_FAIL_INVALID_IAT, \
    FAST_FAIL_HEAP_METADATA_CORRUPTION, \
    FAST_FAIL_PAYLOAD_RESTRICTION_VIOLATION, \
    FAST_FAIL_LOW_LABEL_ACCESS_DENIED, \
    FAST_FAIL_ENCLAVE_CALL_FAILURE, \
    FAST_FAIL_UNHANDLED_LSS_EXCEPTON, \
    FAST_FAIL_ADMINLESS_ACCESS_DENIED, \
    FAST_FAIL_UNEXPECTED_CALL, \
    FAST_FAIL_CONTROL_INVALID_RETURN_ADDRESS, \
    FAST_FAIL_UNEXPECTED_HOST_BEHAVIOR, \
    FAST_FAIL_FLAGS_CORRUPTION;

from ..dxConfig import dxConfig;

def fs0GetFastFailDefineName(uFastFailCode):
  for (sPotentialFastFailDefineName, xPotentialFastFailDefineValue) in globals().items():
    if (
      isinstance(xPotentialFastFailDefineValue, int)
      and sPotentialFastFailDefineName.startswith("FAST_FAIL_")
      and xPotentialFastFailDefineValue == uFastFailCode
    ):
      return sPotentialFastFailDefineName;
  return None;

# I can't find much information on most of these exceptions, so this may be incorrect or at least incomplete.
sPotentiallyExploitable = "Potentially exploitable security issue";
dtsFastFailErrorInformation_by_uCode = {
  FAST_FAIL_LEGACY_GS_VIOLATION:               ("OOBW:Stack",    "/GS detected that a stack cookie was modified",              sPotentiallyExploitable),
  FAST_FAIL_VTGUARD_CHECK_FAILURE:             ("VTGuard",       "VTGuard detected an invalid virtual function table cookie",  sPotentiallyExploitable),
  FAST_FAIL_STACK_COOKIE_CHECK_FAILURE:        ("OOBW:Stack",    "/GS detected that a stack cookie was modified",              sPotentiallyExploitable),
  FAST_FAIL_CORRUPT_LIST_ENTRY:                ("CorruptList",   "Safe unlinking detected a corrupted LIST_ENTRY",             sPotentiallyExploitable),
  FAST_FAIL_FATAL_APP_EXIT:                    ("AppExit",       "Unspecified fatal application error.",                       sPotentiallyExploitable),
  FAST_FAIL_GUARD_ICALL_CHECK_FAILURE:         ("CFG",           "Control Flow Guard detected a call to an invalid address",   sPotentiallyExploitable),
};
auErrorCodesForWhichAStackDumpCouldBeUseful = [
  FAST_FAIL_LEGACY_GS_VIOLATION,
  FAST_FAIL_STACK_COOKIE_CHECK_FAILURE,
  FAST_FAIL_INCORRECT_STACK,
  FAST_FAIL_INVALID_CONTROL_STACK,
];

def cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN(oBugReport, oProcess, oWindowsAPIThread, oException):
  # Parameter[0] = fail fast code
  assert len(oException.auParameters) > 0, \
      "Missing fail fast code in parameters!";
  uFastFailCode = oException.auParameters[0];
  if uFastFailCode in dtsFastFailErrorInformation_by_uCode:
    (
      oBugReport.s0BugTypeId,
      oBugReport.s0BugDescription,
      oBugReport.s0SecurityImpact,
    ) = dtsFastFailErrorInformation_by_uCode[uFastFailCode];
  else:
    oBugReport.s0BugTypeId = fs0GetFastFailDefineName(uFastFailCode) or ("FailFast#%d" % uFastFailCode);
    oBugReport.s0BugDescription = "A critical issue was detected (code %X, fail fast code %d: %s)." % \
        (oException.uCode, uFastFailCode, sFastFailCodeDescription);
    oBugReport.s0SecurityImpact = "Unknown";
  # Add any additional parameters (I have yet to find out what these mean)
  if len(oException.auParameters) == 2:
    oBugReport.s0BugDescription += "Additional parameter: %d/0x%X" % (oException.auParameters[1], oException.auParameters[1]);
  elif len(oException.auParameters) > 2:
    oBugReport.s0BugDescription += "Additional parameters: [ %s ]." % " | ".join(["%d/0x%X" % (u, u) for u in oException.auParameters[1:]]);
  
  if oProcess.oCdbWrapper.bGenerateReportHTML and uFastFailCode in auErrorCodesForWhichAStackDumpCouldBeUseful:
    u0StackPointer = oWindowsAPIThread.fu0GetRegister(b"*sp");
    if u0StackPointer is not None:
      uStackPointer = u0StackPointer;
      # TODO: Call !teb, parse "StackLimit:", trim stack memory dump if needed.
      uSize = dxConfig["uStackDumpSizeInPointers"] * oProcess.uPointerSize;
      if uSize > dxConfig["uMaxMemoryDumpSize"]:
        uSize = dxConfig["uMaxMemoryDumpSize"];
      oBugReport.fAddMemoryDump(uStackPointer, uStackPointer + uSize, "Stack");
      oBugReport.atxMemoryRemarks.append(("Stack pointer", uStackPointer, oProcess.uPointerSize));
  return oBugReport;
