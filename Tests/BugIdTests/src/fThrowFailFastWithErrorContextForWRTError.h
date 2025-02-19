#define WIN32_LEAN_AND_MEAN

#include <unknwn.h>
#include <windows.h>

VOID fThrowFailFastWithErrorContextForWRTError(
  const WCHAR* sHRESULTArgument,
  const WCHAR* sErrorMessageArgument,
  BOOL bLanguageError
);