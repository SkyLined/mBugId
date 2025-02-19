#define WIN32_LEAN_AND_MEAN

#include <windows.h>

#include "mMemory.h"

VOID fFreeAllocatedHeapMemory() {
  if (gbAllocatedHeapMemoryBlock) {
    HANDLE hHeap = GetProcessHeap();
    HeapFree(hHeap, 0, gpMemoryBlock);
    gbAllocatedHeapMemoryBlock = FALSE;
  };
};
