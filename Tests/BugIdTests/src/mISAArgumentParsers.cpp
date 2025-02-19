#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )

#include <tchar.h>
#include <windows.h>

#include "mISA.h"

// Use Instruction Set Architecture (ISA) specific (unsigned) integers:
#ifdef _WIN64
  #define fuGetISAINTForStringWithBase _wcstoi64
  #define fuGetISAUINTForStringWithBase _wcstoui64
#else
  #define fuGetISAINTForStringWithBase wcstol
  #define fuGetISAUINTForStringWithBase wcstoul
#endif

#define fuGetUINT32ForStringWithBase wcstoul

VOID fReportErrorAndExit(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument,
  WCHAR* sEndOfString
) {
  fwprintf(stderr, L"✘ Argument %s must be %s, not %s\r\n", sArgumentName, sArgumentType, sArgument);
  fwprintf(stderr, L"  %s\r\n  ", sArgument);
  for (WCHAR* pChar = (WCHAR*)sArgument; pChar != sEndOfString; pChar++) {
    fwprintf(stderr, L" ");
  };
  fwprintf(stderr, L"^\r\n");
  ExitProcess(1);
};

DWORD fdwGetDWORDForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
) {
  INT iBase = 10;
  if (sArgument[0] == L'0' && sArgument[1] == L'x') {
    sArgument += 2; iBase = 16;
  };
  WCHAR* sEndOfString;
  DWORD dwResult = (DWORD)fuGetUINT32ForStringWithBase(sArgument, &sEndOfString, iBase);
  if (*sEndOfString != 0) fReportErrorAndExit(sArgumentName, sArgumentType, sArgument, sEndOfString);
  return dwResult;
};

HRESULT fhGetHRESULTForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
) {
  INT iBase = 10;
  if (sArgument[0] == L'0' && sArgument[1] == L'x') {
      sArgument += 2; iBase = 16;
  };
  WCHAR* sEndOfString;
  HRESULT hResult = (HRESULT)fuGetUINT32ForStringWithBase(sArgument, &sEndOfString, iBase);
  if (*sEndOfString != 0) fReportErrorAndExit(sArgumentName, sArgumentType, sArgument, sEndOfString);
  return hResult;
};

ISAUINT fuGetISAUINTForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
) {
  INT iBase = 10;
  if (sArgument[0] == L'0' && sArgument[1] == L'x') {
    sArgument += 2; iBase = 16;
  };
  WCHAR* sEndOfString;
  ISAUINT uNumber = fuGetISAUINTForStringWithBase(sArgument, &sEndOfString, iBase);
  if (*sEndOfString != 0) fReportErrorAndExit(sArgumentName, sArgumentType, sArgument, sEndOfString);
  return uNumber;
};

ISAINT fiGetISAINTForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
) {
  INT iBase = 10;
  BOOL bNegative = FALSE;
  if (sArgument[0] == L'-') {
    sArgument += 1; bNegative = TRUE;
  }
  if (sArgument[0] == L'0' && sArgument[1] == L'x') {
    sArgument += 2; iBase = 16;
  };
  WCHAR* sEndOfString;
  ISAINT iNumber = fuGetISAINTForStringWithBase(sArgument, &sEndOfString, iBase);
  if (*sEndOfString != 0) fReportErrorAndExit(sArgumentName, sArgumentType, sArgument, sEndOfString);
  if (bNegative) {
    iNumber = -iNumber;
  };
  return iNumber;
};
