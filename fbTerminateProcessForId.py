import time;
from mWindowsAPI import *;
from fdsProcessesExecutableName_by_uId import fdsProcessesExecutableName_by_uId;

def fbTerminateProcessForId(uProcessId):
  # Try to open the process so we can terminate it...
  bTerminated = False;
  uTerminateProcessError = None;
  hProcess = KERNEL32.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, FALSE, uProcessId);
  if hProcess:
    # We can open it, try to terminate it.
    if KERNEL32.TerminateProcess(hProcess, 0):
      # Success!
      bTerminated = True;
    else:
      # Failed to terminate. This is acceptable if the process is already
      # terminated, which we will find out below.
      uTerminateProcessError = KERNEL32.GetLastError();
  else:
    # Failed to open the process for termination. Try to open the process to
    # see if it's still running...
    hProcess = KERNEL32.OpenProcess(SYNCHRONIZE, FALSE, uProcessId);
    if not hProcess:
      # We cannot open the process. This means it must not exist, or something
      # is wrong:
      assert uProcessId not in fdsProcessesExecutableName_by_uId(), \
          "OpenProcess(0x%08X, FALSE, %d/0x%X) => Error 0x%08X (after %d tries)" % \
          (PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, \
          uProcessId, uProcessId, KERNEL32.GetLastError(), uTryIndex + 1);
      # The process does not exist, assume it was terminated long ago, but not
      # by this function.
      return False;
  # The process should by now have been terminated...give it one second to die:
  assert KERNEL32.WaitForSingleObject(hProcess, 1000) == WAIT_OBJECT_0, \
    uTerminateProcessError is None and (
      "WaitForSingleObject(0x%08X, 1000) => Error 0x%08X" % \
      (hProcess, KERNEL32.GetLastError())
    ) or (
      "TerminateProcess(0x%08X, 0) => Error 0x%08X, WaitForSingleObject(0x%08X, 1000) => Error 0x%08X" % \
      (hProcess, uTerminateProcessError, hProcess, KERNEL32.GetLastError())
    );  
  KERNEL32.CloseHandle(hProcess);
  return bTerminated;