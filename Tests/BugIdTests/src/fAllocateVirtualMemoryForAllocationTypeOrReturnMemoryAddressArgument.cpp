#define WIN32_LEAN_AND_MEAN
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )
// disable warnings about Spectre mitigations
#pragma warning( disable : 5045 )

#include <wchar.h>
#include <windows.h>

#include "mISAArgumentParsers.h"
#include "mMemory.h"

VOID fAllocateVirtualMemoryForAllocationTypeOrReturnMemoryAddressArgument(
  const WCHAR* sAllocationTypeOrMemoryAddressArgument
) {
  if (_wcsicmp(sAllocationTypeOrMemoryAddressArgument, L"Unallocated") == 0) {
    gpMemoryBlock = VirtualAlloc(NULL, 0x100, MEM_COMMIT, PAGE_NOACCESS);
    if (gpMemoryBlock == NULL) {
      fwprintf(stderr, L"✘ VirtualAlloc(NULL, 0x100, MEM_COMMIT, PAGE_NOACCESS) failed.\r\n");
      ExitProcess(1);
    };
    if (!VirtualFree(gpMemoryBlock, 0, MEM_RELEASE)) {
      fwprintf(stderr, L"✘ VirtualFree(0x%p, 0, MEM_RELEASE) failed.\r\n", gpMemoryBlock);
      ExitProcess(1);
    };
    wprintf(L"• Created freed memory at 0x%p.\r\n", gpMemoryBlock);
  } else if (_wcsicmp(sAllocationTypeOrMemoryAddressArgument, L"Reserved") == 0) {
    gpMemoryBlock = VirtualAlloc(NULL, 0x100, MEM_RESERVE, PAGE_NOACCESS);
    if (gpMemoryBlock == NULL) {
      fwprintf(stderr, L"✘ VirtualAlloc(NULL, 0x100, MEM_RESERVE, PAGE_NOACCESS) failed.\r\n");
      ExitProcess(1);
    };
    wprintf(L"• Created reserved memory at address 0x%p.\r\n", gpMemoryBlock);
  } else if (_wcsicmp(sAllocationTypeOrMemoryAddressArgument, L"NoAccess") == 0) {
    gpMemoryBlock = VirtualAlloc(NULL, 0x100, MEM_COMMIT, PAGE_NOACCESS);
    if (gpMemoryBlock == NULL) {
      fwprintf(stderr, L"✘ VirtualAlloc(NULL, 0x100, MEM_COMMIT, PAGE_NOACCESS) failed.\r\n");
      ExitProcess(1);
    };
    wprintf(L"• Created non-accessible memory at address 0x%p.\r\n", gpMemoryBlock);
  } else if (_wcsicmp(sAllocationTypeOrMemoryAddressArgument, L"GuardPage") == 0) {
    gpMemoryBlock = VirtualAlloc(NULL, 0x100, MEM_COMMIT, PAGE_EXECUTE_READWRITE | PAGE_GUARD);
    if (gpMemoryBlock == NULL) {
      fwprintf(stderr, L"✘ VirtualAlloc(NULL, 0x100, MEM_COMMIT, PAGE_EXECUTE_READWRITE | PAGE_GUARD) failed.\r\n");
      ExitProcess(1);
    };
    wprintf(L"• Created a guard page at address 0x%p.\r\n", gpMemoryBlock);
  } else {
    gpMemoryBlock = (PVOID)fuGetISAUINTForArgument(
      L"<AllocationType> or <Address>",
      L"\"Unallocated\", \"Reserved\", \"NoAccess\", \"GuardPage\", or a UINT address to use",
      sAllocationTypeOrMemoryAddressArgument
    );
  };
};
