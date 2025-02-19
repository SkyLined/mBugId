#define WIN32_LEAN_AND_MEAN

#include <wchar.h>
#include <windows.h>

__forceinline VOID fAccessHeapOrStackMemoryBlock(
  const WCHAR* sHeapOrStackArgument,
  const WCHAR* sAccessTypeArgument,
  const WCHAR* sBlockSizeArgument,
  const WCHAR* sAccessStartOffsetArgument,
  const WCHAR* sAccessSizeArgument,
  INT iStep
);