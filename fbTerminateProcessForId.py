from mWindowsAPI import *;

def fbTerminateProcessForId(uProcessId):
  hProcess = KERNEL32.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, FALSE, uProcessId);
  assert hProcess != 0, \
      "OpenProcess(0x%08X, FALSE, %d/0x%X) => Error 0x%08X" % \
      (PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, uProcessId, uProcessId, KERNEL32.GetLastError());
  try:
    dwExitCode = DWORD(0);
#    assert KERNEL32.GetExitCodeProcess(hProcess, POINTER(dwExitCode)), \
#        "GetExitCodeProcess(0x%08X, 0x%08X) => Error 0x%08X" % \
#        (hProcess, POINTER(dwExitCode), KERNEL32.GetLastError());
    if KERNEL32.WaitForSingleObject(hProcess, 0) == WAIT_OBJECT_0:
      # The process is already terminated.
      bTerminated = False;
    else:
      bTerminated = True;
      assert KERNEL32.TerminateProcess(hProcess, 0), \
          "TerminateProcess(0x%08X) => Error 0x%08X" % \
          (hProcess, KERNEL32.GetLastError());
      # Give it one second to die.
      assert KERNEL32.WaitForSingleObject(hProcess, 1000) == WAIT_OBJECT_0, \
          "WaitForSingleObject(0x%08X, 1000) => Error 0x%08X" % \
          (hProcess, KERNEL32.GetLastError());
  finally:
    KERNEL32.CloseHandle(hProcess);
  
  return bTerminated;