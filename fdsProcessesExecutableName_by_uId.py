from mWindowsAPI import *;

def fdsProcessesExecutableName_by_uId():
  dsProcessExecutableName_by_uIds = {};
  hProcessesSnapshot = KERNEL32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
  assert hProcessesSnapshot != INVALID_HANDLE_VALUE, \
      "CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0) => Error 0x%08X" % KERNEL32.GetLastError();
  oProcessEntry32 = PROCESSENTRY32W();
  oProcessEntry32.dwSize = SIZEOF(oProcessEntry32);
  bGotProcess = KERNEL32.Process32FirstW(hProcessesSnapshot, POINTER(oProcessEntry32))
  bFirstProcess = True;
  while bGotProcess:
    bFirstProcess = False;
    dsProcessExecutableName_by_uIds[oProcessEntry32.th32ProcessID] = oProcessEntry32.szExeFile;
    bGotProcess = KERNEL32.Process32NextW(hProcessesSnapshot, POINTER(oProcessEntry32));
  assert KERNEL32.GetLastError() == WIN32_FROM_HRESULT(ERROR_NO_MORE_FILES), \
      "Process32%sW(0x%08X, ...) => Error 0x%08X" % \
      (bFirstProcess and "First" or "Next", hProcessesSnapshot, KERNEL32.GetLastError());
  assert KERNEL32.CloseHandle(hProcessesSnapshot), \
      "CloseHandle(0x%08X) => Error 0x%08X" % \
      (hProcessesSnapshot.value, KERNEL32.GetlastError());
  return dsProcessExecutableName_by_uIds;

