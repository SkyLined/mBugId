#define WIN32_LEAN_AND_MEAN

#include <wchar.h>
#include <windows.h>

#include "fbAllocateHeapOrSetRequiredStackMemoryAndReturnFalseForBlockSizeAndMemoryTypeArguments.h"

// we need the `alloca` call to be inline, so we use a #define that calls a
// function to do most of the work and then return FALSE if we need to do the
// alloca, which is done inline.
#define fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments( \
  sBlockSizeArgument, \
  sHeapOrStackArgument \
) \
  if (!fbAllocateHeapOrSetRequiredStackMemoryAndReturnFalseForBlockSizeAndMemoryTypeArguments( \
    sBlockSizeArgument, \
    sHeapOrStackArgument \
  )) { \
    gpMemoryBlock = alloca(guMemoryBlockSize); \
    wprintf(L"• Created a %IX byte stack block at address 0x%p.\r\n", guMemoryBlockSize, gpMemoryBlock); \
  }

