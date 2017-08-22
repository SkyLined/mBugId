import mWindowsDefines;
from dxConfig import dxConfig;

daxExceptionHandling = {
  "sxe": [ # break on first chance exceptions
    # To be able to track which processes are running at any given time while the application being debugged, cpr and
    # epr must be enabled. Additionally, if epr is disabled the debugger will silently exit when the application
    # terminates. To distinguish this from other unexpected terminations of the debugger, epr must also be enabled.
    "cpr", "ibp", "epr",
    "aph", # Application has stopped responding
    mWindowsDefines.STATUS_ACCESS_VIOLATION,
    mWindowsDefines.STATUS_ASSERTION_FAILURE,
    mWindowsDefines.STATUS_BREAKPOINT,
    mWindowsDefines.STATUS_ARRAY_BOUNDS_EXCEEDED,
    mWindowsDefines.STATUS_DATATYPE_MISALIGNMENT,
    mWindowsDefines.STATUS_FAIL_FAST_EXCEPTION,
    mWindowsDefines.STATUS_GUARD_PAGE_VIOLATION,
    mWindowsDefines.STATUS_ILLEGAL_INSTRUCTION,
    mWindowsDefines.STATUS_IN_PAGE_ERROR,
    mWindowsDefines.STATUS_PRIVILEGED_INSTRUCTION,
    mWindowsDefines.STATUS_STACK_BUFFER_OVERRUN,
    mWindowsDefines.STATUS_STACK_OVERFLOW,
    mWindowsDefines.STATUS_WX86_BREAKPOINT,
    mWindowsDefines.STATUS_WAKE_SYSTEM_DEBUGGER,
  ],
  "sxd": [ # break on second chance exceptions
    mWindowsDefines.STATUS_INTEGER_DIVIDE_BY_ZERO,
    mWindowsDefines.STATUS_INTEGER_OVERFLOW, 
    mWindowsDefines.STATUS_INVALID_HANDLE,
    mWindowsDefines.STATUS_HANDLE_NOT_CLOSABLE,
    # It appears a bug in cdb causes single step exceptions at locations where a breakpoint is set. Since I have never
    # seen a single step exception caused by a bug in an application, I am assuming only detecting second chance single
    # step exceptions will not reduce BugId's effectiveness.
    mWindowsDefines.STATUS_SINGLE_STEP,
    mWindowsDefines.STATUS_WX86_SINGLE_STEP,
    mWindowsDefines.WRT_ORIGINATE_ERROR_EXCEPTION,
  ],
  "sxi": [ # ignored
    "ld", "ud", # Load/unload module
  ],
};

# C++ Exceptions are either handled as second chance exceptions, or ignored completely.
daxExceptionHandling[dxConfig["bIgnoreCPPExceptions"] and "sxi" or "sxd"].append(mWindowsDefines.CPP_EXCEPTION_CODE);
