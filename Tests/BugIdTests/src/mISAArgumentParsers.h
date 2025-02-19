#define WIN32_LEAN_AND_MEAN

#include <tchar.h>
#include <windows.h>

#include "mISA.h"

DWORD fdwGetDWORDForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
);

HRESULT fhGetHRESULTForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
);

ISAUINT fuGetISAUINTForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
);

ISAINT fiGetISAINTForArgument(
  const WCHAR* sArgumentName,
  const WCHAR* sArgumentType,
  const WCHAR* sArgument
);
