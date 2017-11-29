from mWindowsAPI.mDefines import *;
from dxConfig import dxConfig;

def fsExceptionHandlingCdbCommands():
  daxExceptionHandling = {
    "sxe": [ # break on first chance exceptions
      # To be able to track which processes are running at any given time while the application being debugged, cpr and
      # epr must be enabled. Additionally, if epr is disabled the debugger will silently exit when the application
      # terminates. To distinguish this from other unexpected terminations of the debugger, epr must also be enabled.
      "cpr", "ibp", "epr",
      "aph", # Application has stopped responding
      STATUS_ACCESS_VIOLATION,
      STATUS_ASSERTION_FAILURE,
      STATUS_BREAKPOINT,
      STATUS_ARRAY_BOUNDS_EXCEEDED,
      STATUS_DATATYPE_MISALIGNMENT,
      STATUS_FAIL_FAST_EXCEPTION,
      STATUS_GUARD_PAGE_VIOLATION,
      STATUS_ILLEGAL_INSTRUCTION,
      STATUS_IN_PAGE_ERROR,
      STATUS_PRIVILEGED_INSTRUCTION,
      STATUS_STACK_BUFFER_OVERRUN,
      STATUS_STACK_OVERFLOW,
      STATUS_WX86_BREAKPOINT,
      STATUS_WAKE_SYSTEM_DEBUGGER,
    ],
    "sxd": [ # break on second chance exceptions
      STATUS_INTEGER_DIVIDE_BY_ZERO,
      STATUS_INTEGER_OVERFLOW, 
      STATUS_INVALID_HANDLE,
      STATUS_HANDLE_NOT_CLOSABLE,
      # It appears a bug in cdb causes single step exceptions at locations where a breakpoint is set. Since I have never
      # seen a single step exception caused by a bug in an application, I am assuming only detecting second chance single
      # step exceptions will not reduce BugId's effectiveness.
      STATUS_SINGLE_STEP,
      STATUS_WX86_SINGLE_STEP,
    ],
    "sxi": [ # ignored
      "ld", "ud", # Load/unload module
    ],
  };

  # C++ Exceptions are either handled as second chance exceptions, or ignored completely.
  daxExceptionHandling[dxConfig["bIgnoreCPPExceptions"] and "sxi" or "sxd"].extend([
    CPP_EXCEPTION_CODE,
  ]);
  # Windows Runtime exceptions are either handled as second chance exceptions, or ignored completely.
  daxExceptionHandling[dxConfig["bIgnoreWinRTExceptions"] and "sxi" or "sxd"].extend([
    WRT_ORIGINATE_ERROR_EXCEPTION,
    WRT_TRANSFORM_ERROR_EXCEPTION,
  ]);
  asExceptionHandlingCommands = ["sxd *;"];
  # request second chance debugger break for certain exceptions that indicate the application has a bug.
  for sCommand, axExceptions in daxExceptionHandling.items():
    for xException in axExceptions:
      sException = isinstance(xException, str) and xException or ("0x%08X" % xException);
      asExceptionHandlingCommands.append("%s %s;" % (sCommand, sException));
  return "".join(asExceptionHandlingCommands);
