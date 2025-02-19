#define WIN32_LEAN_AND_MEAN

#include <windows.h>

#include "mISA.h"

PVOID   gpMemoryBlock = NULL;
ISAUINT guMemoryBlockSize;
BOOL    gbAllocatedHeapMemoryBlock = FALSE;
