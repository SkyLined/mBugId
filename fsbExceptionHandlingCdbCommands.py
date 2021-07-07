from .dxConfig import dxConfig;
from mWindowsSDK import *;

axExceptionsHandledByBugId = [ # break on first chance exception before application is notified
  # To be able to track which processes are running at any given time while the application being debugged, cpr and
  # epr must be enabled. Additionally, if epr is disabled the debugger will silently exit when the application
  # terminates. To distinguish this from other unexpected terminations of the debugger, epr must also be enabled.
  b"cpr", # create process
  b"epr", # end process
  b"aph", # Application has stopped responding
  STATUS_ACCESS_VIOLATION,
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
  b"out",
];
axExceptionsHandledByApplication = [ # break on second chance exception after the application failed to handle it.
  # Assertion failures report using the NT_ASSERT macro raise a STATUS_ASSERTION_FAILURE exception, but not fatal. 
  # If the application can handle them, let it:
  STATUS_ASSERTION_FAILURE,
];

axIgnoredExceptions = [ # ignored completely
  b"ibp",  # initial breakpoint
  b"ld",   # Load module
  b"ud",   # Unload module
  STATUS_WAKE_SYSTEM_DEBUGGER,
];

def fSetExceptionHandling(daxExceptionHandling, sbHandling, *axExceptions):
  for xException in axExceptions:
    # Remove from previous handling list (if any)
    if xException in daxExceptionHandling[b"sxe"]:
      daxExceptionHandling[b"sxe"].remove(xException);
    elif xException in daxExceptionHandling[b"sxd"]:
      daxExceptionHandling[b"sxd"].remove(xException);
    elif xException in daxExceptionHandling[b"sxi"]:
      daxExceptionHandling[b"sxi"].remove(xException);
    daxExceptionHandling[sbHandling].append(xException);

def fsbExceptionHandlingCdbCommands():
  # Only exceptions not handled by the application are handled by BugId, unless specifically handled or ignored.
  sbExceptionHandlingCommands = b"sxd *;";
  # Make a copy of the default settings so we can modify them without affecting the default.
  daxExceptionHandling = {
    b"sxe": axExceptionsHandledByBugId[:],
    b"sxd": axExceptionsHandledByApplication[:],
    b"sxi": axIgnoredExceptions[:],
  };
  # C++ Exceptions are either handled as second chance exceptions, or ignored completely.
  if dxConfig["bIgnoreAccessViolations"]:
    fSetExceptionHandling(daxExceptionHandling, b"sxi", STATUS_ACCESS_VIOLATION);
  if dxConfig["bIgnoreCPPExceptions"]:
    fSetExceptionHandling(daxExceptionHandling, b"sxi", CPP_EXCEPTION_CODE);
  # Windows Runtime exceptions are either handled as second chance exceptions, or ignored completely.
  if dxConfig["bIgnoreWinRTExceptions"]:
    fSetExceptionHandling(daxExceptionHandling, b"sxi", WRT_ORIGINATE_ERROR_EXCEPTION, WRT_TRANSFORM_ERROR_EXCEPTION);
  # OOM Exceptions are either handled as second chance exceptions, or reported before the application can handle then.
  if dxConfig["bReportBugsForOOMExceptions"]:
    fSetExceptionHandling(daxExceptionHandling, b"sxe",
      ERROR_NOT_ENOUGH_MEMORY,
      ERROR_OUTOFMEMORY,
      ERROR_NOT_ENOUGH_SERVER_MEMORY,
      ERROR_IPSEC_IKE_OUT_OF_MEMORY,
      STATUS_NO_MEMORY,
      0xE0000008, # Chrome specific - not sure yet how to add application specific exceptions in a more elegant way.
    );
  # Create a number of cdb commands to set up exception handling as wanted:
  for sbCommand, axExceptions in daxExceptionHandling.items():
    for xException in axExceptions:
      sbException = isinstance(xException, bytes) and xException or (b"0x%08X" % xException);
      sbExceptionHandlingCommands += b" %s %s;" % (sbCommand, sbException);
  return sbExceptionHandlingCommands;
