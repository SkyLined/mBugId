#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )

#include <wchar.h>
#include <windows.h>

VOID fTestHeapWrongHandle(
  const WCHAR* sBlockSizeArgument
);
