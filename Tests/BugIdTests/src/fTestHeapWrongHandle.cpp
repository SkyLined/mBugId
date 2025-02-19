#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )

#include <stdio.h>
#include <windows.h>

#include "fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments.h"
#include "mMemory.h"

VOID fTestHeapWrongHandle(
  const WCHAR* sBlockSizeArgument
) {
  fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments(
    sBlockSizeArgument, // sBlockSizeArgument
    L"Heap" // sHeapOrStackArgument
  );
  // gpMemoryBlock is now set
  HANDLE hPrimaryHeap = GetProcessHeap();
  HANDLE hSecondaryHeap = HeapCreate(
    0, // DWORD  flOptions
    0, // SIZE_T dwInitialSize,
    0 // SIZE_T dwMaximumSize
  );
  if (hSecondaryHeap == 0) {
    fwprintf(stderr, L"✘ HeapCreate(0, 0, 0) failed.\r\n");
    ExitProcess(1);
  };
  wprintf(L"• Freeing the heap block at 0x%p from heap 0x%p using heap 0x%p...",
      gpMemoryBlock, hPrimaryHeap, hSecondaryHeap);
  HeapFree(hSecondaryHeap, 0, gpMemoryBlock);
};
