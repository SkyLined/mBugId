#define WIN32_LEAN_AND_MEAN
// avoid warning about reading a byte and not using it:
#pragma warning( disable : 4189 )
// disable warnings about inline functions not being inlined.
#pragma warning( disable : 4710 )
// disable warnings about potential exceptions thrown in extern "C" functions
#pragma warning( disable : 5039 )
// disable warnings about Spectre mitigations
#pragma warning( disable : 5045 )
// disable warnings about uninitialize memory (i.e. warnings about potential Use After Free).
#pragma warning( disable : 6001 )
// disable warnings about use of _alloca:
#pragma warning( disable : 6255 )
#pragma warning( disable : 6263 )

#include <crtdbg.h>
#include <exception>
#include <fcntl.h> // _O_U8TEXT
#include <io.h> // _setmode
#include <new>
#include <SDKDDKVer.h>
#include <stdexcept>
#include <wchar.h>
#include <windows.h>

#include "fAccessHeapOrStackMemoryBlock.h"
#include "fAllocateVirtualMemoryForAllocationTypeOrReturnMemoryAddressArgument.h"
#include "fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments.h"
#include "fFreeAllocatedHeapMemory.h"
#include "fTestPureCall.h"
#include "fTestSafeInt.h"
#include "fTestStackRecursion.h"
#include "fTestHeapWrongHandle.h"
#include "fThrowFailFastWithErrorContextForWRTError.h"
#include "mISA.h"
#include "mMASM.h"
#include "mMemory.h"
#include "mISAArgumentParsers.h"

// C++ exception
class cException: public std::exception {};

int wmain(
  const UINT uArgumentsCount,
  const WCHAR* asArguments[]
) {
  // Show Common RunTime errors rather than send a crash dump to Windows Error Reporting.
  _set_abort_behavior( 0, _WRITE_ABORT_MSG);
  // Show Common RunTime errors as debugger messages, rather than ask the user what to do.
  _CrtSetReportMode(_CRT_WARN, _CRTDBG_MODE_FILE | _CRTDBG_MODE_DEBUG);
  _CrtSetReportFile(_CRT_WARN, _CRTDBG_FILE_STDERR);
  _RPT0(_CRT_WARN, "CRT warning message testing\n");
  
  _CrtSetReportMode(_CRT_ERROR, _CRTDBG_MODE_FILE | _CRTDBG_MODE_DEBUG);
  _CrtSetReportFile(_CRT_ERROR, _CRTDBG_FILE_STDERR);
  _RPT0(_CRT_ERROR, "CRT error message testing\n");
  
  _CrtSetReportMode(_CRT_ASSERT, _CRTDBG_MODE_FILE | _CRTDBG_MODE_DEBUG);
  _CrtSetReportFile(_CRT_ASSERT, _CRTDBG_FILE_STDERR);
  _RPT0(_CRT_ASSERT, "CRT assertion message testing\n");
  // disable buffering on stdout and stderr, as output may be put in a buffer
  // and not shown before we trigger an exception.
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);
  // enable UTF-8 output on stdout and stderr
  if (_setmode(_fileno(stdout), _O_U8TEXT) == -1 || _setmode(_fileno(stderr), _O_U8TEXT) == -1) {
    fwprintf(stderr, L"✘ Unable to switch stdout and stderr to UTF-8 output!\r\n");
    ExitProcess(1);
  };
  if (
    uArgumentsCount < 2
    || _wcsicmp(asArguments[1], L"-h") == 0
    || _wcsicmp(asArguments[1], L"-?") == 0
    || _wcsicmp(asArguments[1], L"/h") == 0
    || _wcsicmp(asArguments[1], L"/?") == 0
    || _wcsicmp(asArguments[1], L"--help") == 0
  ) {
    wprintf(L"Usage:\r\n");
    wprintf(L"\r\n");
    wprintf(L"  %s <TestType> [<Arguments>]\r\n", asArguments[0]);
    wprintf(L"\r\n");
    wprintf(L"Where <TestType> and <Arguments> are one of the following:\r\n");
    wprintf(L"\r\n");
    wprintf(L"  AccessViolation <AccessType> ( <AllocationType> | <Address> )\r\n");
    wprintf(L"  Breakpoint\r\n");
    wprintf(L"  BufferOverrun <AllocationType> <AccessType> <BlockSize> <AccessSize>\r\n");
    wprintf(L"  BufferUnderrun <AllocationType> <AccessType> <BlockSize> <AccessSize>\r\n");
    wprintf(L"  C++Exception\r\n");
    wprintf(L"  CorruptStackPointer <AccessType> ( <AllocationType> | <Address> )\r\n");
    wprintf(L"  CPUUsage\r\n");
    wprintf(L"  FailFastException <ExceptionCode> <ExceptionAddress>\r\n");
    wprintf(L"  HeapDoubleFree <BlockSize>\r\n");
    wprintf(L"  HeapMisalignedFree <BlockSize> <Offset>\r\n");
    wprintf(L"  HeapOutOfBounds <AllocationType> <AccessType> <BlockSize> <Offset> [AccessSize]\r\n");
    wprintf(L"  HeapUseAfterFree <AccessType> <BlockSize> <Offset>\r\n");
    wprintf(L"  HeapWrongHandle <BlockSize>\r\n");
    wprintf(L"  IntegerDivideByZero\r\n");
    wprintf(L"  IntegerOverflow\r\n");
    wprintf(L"  IllegalInstruction\r\n");
    wprintf(L"  OOM <AllocationType> <BlockSize>\r\n");
    wprintf(L"  Nop\r\n");
    wprintf(L"  NumberedException <ExceptionCode> <Flags>\r\n");
    wprintf(L"  RecursiveCall <NumberOfCalls>\r\n");
    wprintf(L"  PrivilegedInstruction\r\n");
    wprintf(L"  PureCall\r\n");
    wprintf(L"  SafeInt <Operation> <Signedness> <BitSize>\r\n");
    wprintf(L"  StackExhaustion <BlockSize>\r\n");
    wprintf(L"  WRTLanguageException <HRESULT> <ExceptionMessage>\r\n");
    wprintf(L"  WRTOriginateError <HRESULT> <ErrorMessage>\r\n");
    wprintf(L"\r\n");
    wprintf(L"To get more help for the <Arguments> of a specific <TestType>, use:\r\n");
    wprintf(L"\r\n");
    wprintf(L"  %s <TestType>\r\n", asArguments[0]);
  } else if (_wcsicmp(asArguments[1], L"Nop") == 0) {
    /************************************************************************/
    wprintf(L"• Exiting cleanly...\r\n");
  } else if (_wcsicmp(asArguments[1], L"Breakpoint") == 0) {
    /************************************************************************/
    wprintf(L"• Triggering debug breakpoint...\r\n");
    __debugbreak();
  } else if (_wcsicmp(asArguments[1], L"CPUUsage") == 0) {
    /************************************************************************/
    wprintf(L"• Using 100%% CPU in 1 thread...\r\n");
    while(1){};
  } else if (_wcsicmp(asArguments[1], L"IntegerDivideByZero") == 0) {
    /************************************************************************/
    wprintf(L"• Dividing by zero...\r\n");
    volatile UINT uN = 0;
    uN = 0 / uN;
  } else if (_wcsicmp(asArguments[1], L"IntegerOverflow") == 0) {
    /************************************************************************/
    wprintf(L"• Triggering integer overflow...\r\n");
    fIntegerOverflow(0);
  } else if (_wcsicmp(asArguments[1], L"IllegalInstruction") == 0) {
    /************************************************************************/
    wprintf(L"• Executing illegal instruction...\r\n");
    fIllegalInstruction(0);
  } else if (_wcsicmp(asArguments[1], L"PrivilegedInstruction") == 0) {
    /************************************************************************/
    wprintf(L"• Executing a privileged instruction...\r\n");
    fPrivilegedInstruction(0);
  } else if (_wcsicmp(asArguments[1], L"PureCall") == 0) {
    /************************************************************************/
    fTestPureCall();
  } else if (_wcsicmp(asArguments[1], L"StackExhaustion") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 3) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"StackExhaustion\" <BlockSize>\r\n"
        L"Where:\r\n"
        L"  <BlockSize> = a UINT memory block size to repeatedly allocate on the stack.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    ISAUINT uBlockSize = fuGetISAUINTForArgument(
      L"<BlockSize>",
      L"a UINT memory block size to repeatedly allocate on the stack",
      asArguments[2]
    );
    wprintf(L"• Repeatedly allocating %Id/0x%IX bytes of stack memory...\r\n", uBlockSize, uBlockSize);
    while (1) alloca(uBlockSize);
  } else if (_wcsicmp(asArguments[1], L"RecursiveCall") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 3) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"RecursiveCall\" <NumberOfCalls>\r\n"
        L"Where:\r\n"
        L"  <NumberOfCalls> = a UINT number of functions in each recursion loop.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fTestStackRecursion(asArguments[2]);
  } else if (_wcsicmp(asArguments[1], L"C++Exception") == 0) {
    /************************************************************************/
    wprintf(L"• Throwing C++ exception...\r\n");
    cException oException;
    throw oException;
  } else if (_wcsicmp(asArguments[1], L"FailFastException") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 4) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"FailFastException\" <ExceptionCode> <ExceptionAddress>\r\n"
        L"Where:\r\n"
        L"  <ExceptionCode> = a 32-bit UINT exception code.\r\n"
        L"  <ExceptionAddress> = a UINT exception address in virtual memory.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    EXCEPTION_RECORD oExceptionRecord = {
      fdwGetDWORDForArgument(
        L"<ExceptionCode>", // sArgumentName
        L"a valid positive integer DWORD value", // sArgumentType
        asArguments[2] // sArgument (<ExceptionCode>)
      ),
      EXCEPTION_NONCONTINUABLE, // ExceptionFlags
      NULL, // ExceptionRecord
      (PVOID)fuGetISAUINTForArgument(
        L"<ExceptionAddress>",
        L"a UINT exception address in virtual memory",
        asArguments[3]
      ), // ExceptionAddress
      0, // NumberParameters
      {0}, // ExceptionInformation
    };
    RaiseFailFastException(&oExceptionRecord, NULL, 0);
  } else if (_wcsicmp(asArguments[1], L"WRTOriginateError") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 4) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"WRTOriginateError\" <HRESULT> <ErrorMessage> [<Language>]\r\n"
        L"Where:\r\n"
        L"  <HRESULT>      = a 32-bit UINT value to use as HRESULT error code.\r\n"
        L"  <ErrorMessage> = a string to use as error message.\r\n"
        L"  <Language>     = \"Language\" to use a WRT Originate Language error.\r\n"
        L"                   If not provided, a WRT Originate error is used instead.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    if (uArgumentsCount == 4 || wcslen(asArguments[4]) == 0) {
      fThrowFailFastWithErrorContextForWRTError(
        asArguments[2], // sHRESULTArgument
        asArguments[3], // sErrorMessageArgument
        FALSE // bLanguageError
      );
    } else if (_wcsicmp(asArguments[4], L"Language") == 0) {
      fThrowFailFastWithErrorContextForWRTError(
        asArguments[2], // sHRESULTArgument
        asArguments[3], // sErrorMessageArgument
        TRUE // bLanguageError
      );
    } else {
      fwprintf(stderr, L"✘ <Language> must be \"Language\" or omitted, not %s.\r\n", asArguments[4]);
      ExitProcess(1);
    };
  } else if (_wcsicmp(asArguments[1], L"OOM") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 4) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"OOM\" <AllocationType> <BlockSize>\r\n"
        L"Where:\r\n"
        L"  <AllocationType> = ( \"HeapAlloc\" | \"C++\" | \"Stack\" ).\r\n"
        L"  <BlockSize> = a UINT size of the memory blocks to repeatedly allocate.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    BOOL bHeapAlloc = FALSE, bCPP = FALSE;
    if (_wcsicmp(asArguments[2], L"HeapAlloc") == 0) {
      bHeapAlloc = TRUE;
    } else if (_wcsicmp(asArguments[2], L"C++") == 0) {
      bCPP = TRUE;
    } else if (_wcsicmp(asArguments[2], L"Stack") != 0) {
      fwprintf(stderr, L"✘ <AllocationType> must be \"HeapAlloc\", \"C++\" or \"Stack\", not %s.\r\n", asArguments[2]);
      ExitProcess(1);
    };
    ISAUINT uBlockSize = fuGetISAUINTForArgument(
      L"<BlockSize>",
      L"a UINT size of the memory blocks to repeatedly allocate",
      asArguments[3]
    );
    if (bHeapAlloc) {
      wprintf(L"• Using HeapAlloc to allocate blocks of %Id/0x%IX bytes of heap memory...\r\n", uBlockSize, uBlockSize);
      HANDLE hHeap = GetProcessHeap();
      while (1) HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uBlockSize);
    } else if (bCPP) {
      wprintf(L"• Using new BYTE[...] to allocate blocks of %Id/0x%IX bytes of heap memory...\r\n", uBlockSize, uBlockSize);
      while (1) new BYTE[uBlockSize];
    } else {
      // Stack is a two step process: we cannot use up all memory using
      // the stack, so we use HeapAlloc to allocate memory until that is no
      // longer possible. Once that happens, we use alloca to trigger an
      // exception.
      wprintf(L"• Using HeapAlloc to allocate blocks of %Id/0x%IX bytes of heap memory...\r\n", uBlockSize, uBlockSize);
      HANDLE hHeap = GetProcessHeap();
      while (HeapAlloc(hHeap, 0, uBlockSize));
      wprintf(L"• Using alloca to allocate blocks of %Id/0x%IX bytes of stack memory...\r\n", uBlockSize, uBlockSize);
      while (1) alloca(uBlockSize);
    };
  } else if (_wcsicmp(asArguments[1], L"NumberedException") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 4) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"NumberedException\" <ExceptionCode> <Flags>\r\n"
        L"Where:\r\n"
        L"  <Code>  = a 32-bit DWORD value to use as exception code.\r\n"
        L"  <Flags> = a 32-bit DWORD value to use as exception flags.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    DWORD dwCode = fdwGetDWORDForArgument(
      L"<Code>", // sArgumentName
      L"a valid positive integer DWORD value", // sArgumentType
      asArguments[2] // sArgument (<Code>)
    );
    DWORD dwFlags = fdwGetDWORDForArgument(
      L"<Flags>",
      L"a valid positive integer DWORD value", // sArgumentType
      asArguments[3] // sArgument (<Flags>)
    );
    // TODO: implement arguments?
    RaiseException(dwCode, dwFlags, 0, NULL);
  } else if (_wcsicmp(asArguments[1], L"AccessViolation") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 4) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"AccessViolation\" <AccessType> ( <AllocationType> | <Address> )\r\n"
        L"Where:\r\n"
        L"  <AccessType>     = ( \"Call\" | \"Jump\" | \"Ret\" | \"Read\" | \"Write\" )\r\n"
        L"  <Address>        = a UINT address to use.\r\n"
        L"  <AllocationType> = ( \"Unallocated\" | \"Reserved\" | \"NoAccess\" | \"GuardPage\" )\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAllocateVirtualMemoryForAllocationTypeOrReturnMemoryAddressArgument(
      asArguments[3] // sAllocationTypeOrMemoryAddressArgument
    );
    // gpMemoryBlock is now set
    if (_wcsicmp(asArguments[2], L"Call") == 0) {
      wprintf(L"• Calling address 0x%p...\r\n", gpMemoryBlock);
      fCall(gpMemoryBlock);
    } else if (_wcsicmp(asArguments[2], L"Jump") == 0) {
      wprintf(L"• Jumping to address 0x%p...\r\n", gpMemoryBlock);
      fJump(gpMemoryBlock);
    } else if (_wcsicmp(asArguments[2], L"Ret") == 0) {
      wprintf(L"• Returning to address 0x%p...\r\n", gpMemoryBlock);
      fRet(gpMemoryBlock);
    } else if (_wcsicmp(asArguments[2], L"Read") == 0) {
      wprintf(L"• Reading from address 0x%p...\r\n", gpMemoryBlock);
      BYTE bByte = *(PBYTE)gpMemoryBlock;
    } else if (_wcsicmp(asArguments[2], L"Write") == 0) {
      wprintf(L"• Writing to address 0x%p...\r\n", gpMemoryBlock);
      *(PBYTE)gpMemoryBlock = 0x41;
    } else {
      fwprintf(stderr, L"✘ <AccessType> must be \"Call\", \"Jmp\", \"Ret\", \"Read\", or \"Write\", not %s.\r\n", asArguments[2]);
      ExitProcess(1);
    };
  } else if (_wcsicmp(asArguments[1], L"CorruptStackPointer") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 4) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"CorruptStackPointer\" <AccessType> ( <AllocationType> | <Address> )\r\n"
        L"Where:\r\n"
        L"  <AccessType>     = ( \"Call\" | \"Ret\" | \"Push\" | \"Pop\" )\r\n"
        L"  <AllocationType> = ( \"Unallocated\" | \"Reserved\" | \"NoAccess\" | \"GuardPage\" )\r\n"
        L"  <Address>        = a UINT address to use.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAllocateVirtualMemoryForAllocationTypeOrReturnMemoryAddressArgument(
      asArguments[3] // sAllocationTypeOrMemoryAddressArgument
    );
    // gpMemoryBlock is now set
    if (_wcsicmp(asArguments[2], L"Call") == 0) {
      // call should decrease the stack pointer before writing to it, so
      // to avoid the access violation happening at a lower address than
      // requested we need to compensate for this:
      PVOID pStackPointerAddress = (PVOID)((PBYTE)gpMemoryBlock + sizeof(ISAINT));
      wprintf(L"• Calling a function using 0x%p+%zu as stack pointer...\r\n", gpMemoryBlock, sizeof(ISAINT));
      fCallWithStackPointer(pStackPointerAddress);
    } else if (_wcsicmp(asArguments[2], L"Ret") == 0) {
      wprintf(L"• Returning from a function using 0x%p as stack pointer...\r\n", gpMemoryBlock);
      fRetWithStackPointer(gpMemoryBlock);
    } else if (_wcsicmp(asArguments[2], L"Push") == 0) {
      // push should decrease the stack pointer before writing to it, so
      // to avoid the access violation happening at a lower address than
      // requested we need to compensate for this:
      PVOID pStackPointerAddress = (PVOID)((PBYTE)gpMemoryBlock + sizeof(ISAINT));
      wprintf(L"• Pushing a value on to the stack using 0x%p+%zu as stack pointer...\r\n", gpMemoryBlock, sizeof(ISAINT));
      fPushWithStackPointer(pStackPointerAddress);
    } else if (_wcsicmp(asArguments[2], L"Pop") == 0) {
      wprintf(L"• Popping a value off the stack using 0x%p as stack pointer...\r\n", gpMemoryBlock);
      fPopWithStackPointer(gpMemoryBlock);
    } else {
      fwprintf(stderr, L"✘ <AccessType> must be \"Call\", \"Ret\", \"Push\", or \"Pop\", not %s\r\n", asArguments[2]);
      ExitProcess(1);
    };
  } else if (_wcsicmp(asArguments[1], L"HeapUseAfterFree") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 5) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"HeapUseAfterFree\" <AccessType> <BlockSize> <Offset>\r\n"
        L"Where:\r\n"
        L"  <AccessType> = ( \"Call\" | \"Jump\" | \"Ret\" | \"Read\" | \"Write\" )\r\n"
        L"  <BlockSize>  = a UINT size for the freed heap block.\r\n"
        L"  <Offset>     = an INT offset from the start of the freed heap block.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments(
      asArguments[3], // sBlockSizeArgument
      L"Heap" // sHeapOrStackArgument
    );
    // gpMemoryBlock is now set
    ISAINT iOffset = fiGetISAINTForArgument(
      L"<Offset>",
      L"a UINT size for the freed heap block",
      asArguments[4]
    );
    wprintf(L"• Freeing the heap block at 0x%p...", gpMemoryBlock);
    fFreeAllocatedHeapMemory();
    PVOID pAddress = (PVOID)((PBYTE)gpMemoryBlock + iOffset);
    if (_wcsicmp(asArguments[2], L"Call") == 0) {
      wprintf(L"• Calling offset %Id/0x%IX at address 0x%p in the freed heap block...\r\n",
          iOffset, iOffset, pAddress);
      fCall(pAddress);
    } else if (_wcsicmp(asArguments[2], L"Jump") == 0) {
      wprintf(L"• Jumping to offset %Id/0x%IX at address 0x%p in the freed heap block...\r\n",
          iOffset, iOffset, pAddress);
      fJump(pAddress);
    } else if (_wcsicmp(asArguments[2], L"Ret") == 0) {
      wprintf(L"• Returning to offset %Id/0x%IX at address 0x%p in the freed heap block...\r\n",
          iOffset, iOffset, pAddress);
      fRet(pAddress);
    } else if (_wcsicmp(asArguments[2], L"Read") == 0) {
      wprintf(L"• Reading at offset %Id/0x%IX at address 0x%p in the freed heap block...\r\n",
          iOffset, iOffset, pAddress);
      BYTE bByte = *(PBYTE)pAddress;
    } else if (_wcsicmp(asArguments[2], L"Write") == 0) {
      wprintf(L"• Writing at offset %Id/0x%IX at address 0x%p in the freed heap block...\r\n",
          iOffset, iOffset, pAddress);
      *(PBYTE)pAddress = 0x41;
    } else {
      fwprintf(stderr, L"✘ <AccessType> must be \"Call\", \"Jmp\", \"Read\", or \"Write\", not %s.\r\n", asArguments[2]);
      ExitProcess(1);
    };
  } else if (_wcsicmp(asArguments[1], L"HeapDoubleFree") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 3) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"HeapDoubleFree\" <BlockSize>\r\n"
        L"Where:\r\n"
        L"  <BlockSize>  = a UINT size of the heap block.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments(
      asArguments[2], // sBlockSizeArgument
      L"Heap" // sHeapOrStackArgument
    );
    // gpMemoryBlock is now set
    wprintf(L"• Freeing the heap block at 0x%p...\r\n", gpMemoryBlock);
    fFreeAllocatedHeapMemory();
    wprintf(L"• Freeing the heap block at 0x%p again...\r\n", gpMemoryBlock);
    gbAllocatedHeapMemoryBlock = TRUE; // Pretend it was not just freed.
    fFreeAllocatedHeapMemory(); // And free it again
  } else if (_wcsicmp(asArguments[1], L"HeapMisalignedFree") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 4) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"HeapMisalignedFree\" <BlockSize> <Offset>\r\n"
        L"Where:\r\n"
        L"  <BlockSize> = a UINT size of the memory block.\r\n"
        L"  <Offset>    = an INT offset from the start of the memory block.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAllocateHeapOrStackMemoryForBlockSizeAndMemoryTypeArguments(
      asArguments[2], // sBlockSizeArgument
      L"Heap" // sHeapOrStackArgument
    );
    // gpMemoryBlock is now set
    ISAINT iOffset = fiGetISAINTForArgument(
      L"<Offset>",
      L"an INT offset from the start of the memory block",
      asArguments[3]
    );
    // Offset the memory block pointer.
    gpMemoryBlock = (PVOID)((PBYTE)gpMemoryBlock + iOffset);
    // free the memory using an misaligned pointer
    fFreeAllocatedHeapMemory();
  } else if (_wcsicmp(asArguments[1], L"HeapWrongHandle") == 0) {
    //--------------------------------------------------------------------------
    // Allocate memory on the heap, then create a second heap and use it to try
    // to free the memory.
    if (uArgumentsCount < 3) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"HeapWrongHandle\" <BlockSize>\r\n"
        L"Where:\r\n"
        L"  <BlockSize>      = a UINT size of the memory block to use.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fTestHeapWrongHandle(
      asArguments[2]
    );
  } else if (_wcsicmp(asArguments[1], L"OutOfBounds") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 6) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"HeapOutOfBounds\" <HeapOrStack> <AccessType> <BlockSize> <Offset> [<AccessSize>]\r\n"
        L"Where:\r\n"
        L"  <HeapOrStack>  = ( \"Heap\" | \"Stack\" )\r\n"
        L"  <AccessType>   = ( \"Read\" | \"Write\" )\r\n"
        L"  <BlockSize>    = a UINT size of the memory block.\r\n"
        L"  <Offset>       = an INT offset from the start of the memory block.\r\n"
        L"  [<AccessSize>] = an optional UINT number of bytes to access starting at the offset.\r\n"
        L"                   The default number of bytes to access is 1.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAccessHeapOrStackMemoryBlock(
      asArguments[2], // sHeapOrStackArgument
      asArguments[3], // sAccessTypeArgument
      asArguments[4], // sBlockSizeArgument
      asArguments[5], // sAccessStartOffsetArgument
      uArgumentsCount < 7 ? L"1" : asArguments[6], // sAccessSizeArgument
      +1 // uStep
    );
  } else if (_wcsicmp(asArguments[1], L"BufferOverrun") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 6) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"BufferOverrun\" <HeapOrStack> <AccessType> <BlockSize> <AccessSize>\r\n"
        L"Where:\r\n"
        L"  <HeapOrStack>  = ( \"Heap\" | \"Stack\" )\r\n"
        L"  <AccessType>   = ( \"Read\" | \"Write\" )\r\n"
        L"  <BlockSize>    = a UINT size of the memory block.\r\n"
        L"  <AccessSize>  = a UINT number of bytes to access beyond the end of the block.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAccessHeapOrStackMemoryBlock(
      asArguments[2], // sHeapOrStackArgument
      asArguments[3], // sAccessTypeArgument
      asArguments[4], // sBlockSizeArgument
      asArguments[4], // sAccessStartOffsetArgument (<BlockSize> so we start at the end of the block)
      asArguments[5], // sAccessSizeArgument
      +1 // uStep
    );
  } else if (_wcsicmp(asArguments[1], L"BufferUnderrun") == 0) {
    /************************************************************************/
    if (uArgumentsCount < 6) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"BufferUnderrun\" <HeapOrStack> <AccessType> <BlockSize> <AccessSize>\r\n"
        L"Where:\r\n"
        L"  <HeapOrStack>  = ( \"Heap\" | \"Stack\" )\r\n"
        L"  <AccessType>   = ( \"Read\" | \"Write\" )\r\n"
        L"  <BlockSize>    = a UINT size of the memory block.\r\n"
        L"  <AccessSize> = a UINT number of bytes to access before the end of the block.\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fAccessHeapOrStackMemoryBlock(
      asArguments[2], // sHeapOrStackArgument
      asArguments[3], // sAccessTypeArgument
      asArguments[4], // sBlockSizeArgument
      L"0", // sAccessStartOffsetArgument (0 so we start at the start of the block)
      asArguments[5], // sAccessSizeArgument
      -1 // uStep (move down towards address 0).
    );
  } else if (_wcsicmp(asArguments[1], L"SafeInt") == 0) {
    //--------------------------------------------------------------------------
    if (uArgumentsCount < 5) {
      wprintf((
        L"Usage:\r\n"
        L"  %s \"SafeInt\" <Operation> <Signedness> <BitSize>\r\n"
        L"Where:\r\n"
        L"  <Operation>    = ( \"++\" | \"--\" | \"*\" | \"truncate\" | \"signedness\" )\r\n"
        L"  <Signedness>   = ( \"signed\" | \"unsigned\" )\r\n"
        L"  <BitSize>      = ( \"8\" | \"16\" | \"32\" | \"64\" )\r\n"
      ), asArguments[0]);
      ExitProcess(1);
    };
    fTestSafeInt(
      asArguments[2], // sOperationArgument
      asArguments[3], // sSignednessArgument
      asArguments[4] // sBitSizeArgument
    );
  } else {
    fwprintf(stderr, L"✘ <TestType> %s is not known.\r\n", asArguments[1]);
    ExitProcess(1);
  };
  return 0;
};
