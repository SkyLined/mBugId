#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )
// disable warnings about Spectre mitigations
#pragma warning( disable : 5045 )
// disable warnings about alloca potentially throwing an exception
#pragma warning( disable : 6255 )

#include <wchar.h>
#include <windows.h>

#include "mISAArgumentParsers.h"
#include "mMemory.h"

BOOL fbAllocateHeapOrSetRequiredStackMemoryAndReturnFalseForBlockSizeAndMemoryTypeArguments(
  const WCHAR* sBlockSizeArgument, 
  const WCHAR* sHeapOrStackArgument 
) { 
  BOOL bAllocateHeapMemory = _wcsicmp(sHeapOrStackArgument, L"Heap") == 0;
  guMemoryBlockSize = fuGetISAUINTForArgument(
    L"<BlockSize>",
    L"a UINT size for the memory block",
    sBlockSizeArgument
  );
  if (bAllocateHeapMemory) {
    HANDLE hHeap = GetProcessHeap();
    gpMemoryBlock = HeapAlloc(hHeap, 0, guMemoryBlockSize);
    if (!gpMemoryBlock) {
      fwprintf(stderr, L"✘ HeapAlloc(0x%p, 0, 0x%IX) failed.\r\n", hHeap, guMemoryBlockSize);
      ExitProcess(1);
    };
    gbAllocatedHeapMemoryBlock = TRUE;
    wprintf(L"• Created a %IX byte heap block at address 0x%p.\r\n", guMemoryBlockSize, gpMemoryBlock);
    return TRUE;
  } else if (_wcsicmp(sHeapOrStackArgument, L"Stack") == 0) {
    return FALSE;
  } else {
    fwprintf(stderr, L"✘ <HeapOrStack> must be\"Heap\" or \"Stack\", not %s.\r\n", sHeapOrStackArgument);
    ExitProcess(1);
  };
};
