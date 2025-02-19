#define WIN32_LEAN_AND_MEAN

#include <wchar.h>
#include <windows.h>

BOOL fbAllocateHeapOrSetRequiredStackMemoryAndReturnFalseForBlockSizeAndMemoryTypeArguments(
  const WCHAR* sBlockSizeArgument,
  const WCHAR* sHeapOrStackArgument
);
