#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )

#include <wchar.h>
#include <windows.h>

#include "fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments.h"
#include "fFreeAllocatedHeapMemory.h"
#include "mMemory.h"
#include "mISAArgumentParsers.h"

// Writing to the stack may overwrite local variables. To avoid this interfering
// with our code, global variables are used.
PBYTE gpAccessAddress;
ISAUINT guCounter;
BOOL gbRead;
INT giStep;
BYTE gbByte = 0x41;
VOID fAccessHeapOrStackMemoryBlock(
  const WCHAR* sHeapOrStackArgument,
  const WCHAR* sAccessTypeArgument,
  const WCHAR* sBlockSizeArgument,
  const WCHAR* sAccessStartOffsetArgument,
  const WCHAR* sAccessSizeArgument,
  INT iStep
) {
  fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments(
    sBlockSizeArgument,
    sHeapOrStackArgument
  );
  ISAINT iOffset = fiGetISAINTForArgument(
    L"<Offset>",
    L"an INT offset from the start of the memory block",
    sAccessStartOffsetArgument
  );
  ISAUINT uAccessSize = fuGetISAUINTForArgument(
    L"<AccessSize>",
    L"a UINT number of bytes to access starting at the offset",
    sAccessSizeArgument
  );
  if (_wcsicmp(sAccessTypeArgument, L"Read") == 0) {
    wprintf(L"• Reading %Id/0x%IX bytes starting at offset %Id/0x%IX from the start of the memory block...\r\n",
        uAccessSize, uAccessSize, iOffset, iOffset);
    gbRead = TRUE;
  } else if (_wcsicmp(sAccessTypeArgument, L"Write") == 0) {
    gbRead = FALSE;
    wprintf(L"• Writing %Id/0x%IX bytes starting at offset %Id/0x%IX from the start of the memory block...\r\n",
        uAccessSize, uAccessSize, iOffset, iOffset);
  } else {
    fwprintf(stderr, L"✘ <AccessType> must be \"Read\" or \"Write\", not %s.\r\n", sAccessTypeArgument);
    ExitProcess(1);
  };
  gpAccessAddress = (PBYTE)gpMemoryBlock + iOffset;
  giStep = iStep;
  guCounter = uAccessSize;
  // Beyond this point, locals should no longer be accessed, as these are on the
  // stack and may be corrupted when we are writing to memory.
  while (guCounter--) {
    // we we are going down, we want to change the address before reading/writing
    if (giStep < 0) gpAccessAddress += giStep;
    if (gbRead) {
      gbByte = *gpAccessAddress;
    } else {
      *gpAccessAddress = gbByte;
    };
    // we we are going up, we want to change the address after reading/writing
    if (giStep > 0) gpAccessAddress += giStep;
  };
  fFreeAllocatedHeapMemory();
};
