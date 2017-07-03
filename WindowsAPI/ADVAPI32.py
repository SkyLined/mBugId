from cDLL import cDLL;
from Types import *;

ADVAPI32 = cDLL("Advapi32.dll");
ADVAPI32.fAddFunction(BOOL, "GetTokenInformation", HANDLE, TOKEN_INFORMATION_CLASS, LPVOID, DWORD, PDWORD);
ADVAPI32.fAddFunction(POINTER(UCHAR), "GetSidSubAuthorityCount", POINTER(SID));
ADVAPI32.fAddFunction(POINTER(DWORD), "GetSidSubAuthority", POINTER(SID), DWORD);
