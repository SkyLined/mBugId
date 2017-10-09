from mWindowsAPI import *;

hProcessHeap = None;
def cProcess__fuGetIntegrityLevel(oProcess):
  global hProcessHeap;
  if hProcessHeap is None:
    hProcessHeap = KERNEL32.GetProcessHeap();
    assert hProcessHeap != 0, \
        "GetProcessHeap() => Error 0x%08X" % KERNEL32.GetLastError();
  hProcess = KERNEL32.OpenProcess(PROCESS_QUERY_INFORMATION, FALSE, oProcess.uId);
  if hProcess == 0:
    return None;
  try:
    hToken = HANDLE();
    if not KERNEL32.OpenProcessToken(hProcess, DWORD(TOKEN_QUERY), PHANDLE(hToken)):
      return None;
    try:
      # Find out how large a TOKEN_MANDATORY_LABEL struct is:
      dwTokenMandatoryLabelSize = DWORD();
      assert not ADVAPI32.GetTokenInformation(hToken, TokenIntegrityLevel, None, 0, PDWORD(dwTokenMandatoryLabelSize)), \
          "GetTokenInformation(...) succeeded unexpectedly";
      assert KERNEL32.GetLastError() == ERROR_INSUFFICIENT_BUFFER, \
          "GetTokenInformation(...) => Error 0x%08X" % KERNEL32.GetLastError();
      # Allocate memory to store a TOKEN_MANDATORY_LABEL struct:
      pTokenMandatoryLabelMemoryAddress = KERNEL32.HeapAlloc(hProcessHeap, HEAP_ZERO_MEMORY, dwTokenMandatoryLabelSize.value)
      try:
        # Get the TOKEN_MANDATORY_LABEL struct:
        poTokenMandatoryLabel = CAST(pTokenMandatoryLabelMemoryAddress, POINTER(TOKEN_MANDATORY_LABEL));
        if not ADVAPI32.GetTokenInformation(hToken, TokenIntegrityLevel, poTokenMandatoryLabel, dwTokenMandatoryLabelSize, PDWORD(dwTokenMandatoryLabelSize)):
          return None;
        oTokenMandatoryLabel = poTokenMandatoryLabel.contents;
        # Found out the index of the last Sid Sub Authority
        puSidSubAuthorityCount = ADVAPI32.GetSidSubAuthorityCount(oTokenMandatoryLabel.Label.Sid);
        uLastSidSubAuthorityIndex = puSidSubAuthorityCount.contents.value - 1;
        # Get the last Sid Sub Authority
        pdwLastSidSubAuthority= ADVAPI32.GetSidSubAuthority(oTokenMandatoryLabel.Label.Sid, uLastSidSubAuthorityIndex);
        dwIntegrityLevel = pdwLastSidSubAuthority.contents.value;
        return dwIntegrityLevel;
      finally:
        KERNEL32.HeapFree(hProcessHeap, 0, pTokenMandatoryLabelMemoryAddress);
    finally:
      KERNEL32.CloseHandle(hToken);
  finally:
    KERNEL32.CloseHandle(hProcess);
