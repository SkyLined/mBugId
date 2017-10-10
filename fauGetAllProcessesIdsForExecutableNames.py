from mWindowsAPI import *;

def fauGetAllProcessesIdsForExecutableNames(*asExecutableNames):
  # Compare is going to be case insensitive, might as wel remove case now.
  asExecutableNames = [unicode(sExecutableName).lower() for sExecutableName in asExecutableNames];
  auProcessIds = [];
  # Repeatedly find all processes and kill those that have the binary loaded as a module until none or left.
  # This is repeated because one of them may spawn a new child after we got the list of processes but before we get
  # a chance to kill it, which would cause us to not kill the new child even if it does load one the the binaries.
  hProcessesSnapshot = KERNEL32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
  assert hProcessesSnapshot != INVALID_HANDLE_VALUE, \
      "CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0) => Error 0x%08X" % KERNEL32.GetLastError();
  
  oProcessEntry32 = PROCESSENTRY32W();
  oProcessEntry32.dwSize = SIZEOF(oProcessEntry32);
  bGotProcess = KERNEL32.Process32FirstW(hProcessesSnapshot, POINTER(oProcessEntry32))
  bFirstProcess = True;
  while bGotProcess:
    bFirstProcess = False;
    if oProcessEntry32.szExeFile.lower() in asExecutableNames:
      auProcessIds.append(oProcessEntry32.th32ProcessID);
    bGotProcess = KERNEL32.Process32NextW(hProcessesSnapshot, POINTER(oProcessEntry32));
  assert KERNEL32.GetLastError() == WIN32_FROM_HRESULT(ERROR_NO_MORE_FILES), \
      "Process32%sW(0x%08X, ...) => Error 0x%08X" % \
      (bFirstProcess and "First" or "Next", hProcessesSnapshot, KERNEL32.GetLastError());
  assert KERNEL32.CloseHandle(hProcessesSnapshot), \
      "CloseHandle(0x%08X) => Error 0x%08X" % \
      (hProcessesSnapshot.value, KERNEL32.GetlastError());
  return auProcessIds;

