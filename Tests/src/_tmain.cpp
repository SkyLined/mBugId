#include <SDKDDKVer.h>
#include <stdio.h>
#include <tchar.h>
#include <windows.h>
#include <exception>
#include <new>

#define BYTE_TO_WRITE 0x41

// Use Instruction Set Architecture (ISA) specific (unsigned) integers:
#ifdef _WIN64
  #define ISAINT signed __int64
  #define ISAUINT signed __int64
  #define String_2_ISAINT _tcstoi64
  #define String_2_ISAUINT _tcstoui64
#else
  #define ISAINT INT
  #define ISAUINT UINT
  #define String_2_ISAINT _tcstol
  #define String_2_ISAUINT _tcstoul
#endif

VOID* fpParsePointer(_TCHAR* sInput) {
  INT uBase = 10;
  if (sInput[0] == _T('0') && sInput[1] == _T('x')) {
    sInput += 2; uBase = 16;
  };
  return (VOID*)String_2_ISAUINT(sInput, NULL, uBase);
};
DWORD fdwParseDWORD(_TCHAR* sInput) {
  UINT uBase = 10;
  if (sInput[0] == _T('0') && sInput[1] == _T('x')) {
    sInput += 2; uBase = 16;
  };
  return (DWORD)_tcstoul(sInput, NULL, uBase);
};
ISAUINT fuParseNumber(_TCHAR* sInput) {
  UINT uBase = 10;
  if (sInput[0] == _T('0') && sInput[1] == _T('x')) {
    sInput += 2; uBase = 16;
  };
  return String_2_ISAUINT(sInput, NULL, uBase);
};
ISAINT fiParseNumber(_TCHAR* sInput) {
  UINT uBase = 10;
  ISAINT iSignMultiplier = 1;
  if (sInput[0] == _T('-')) {
    sInput += 1; iSignMultiplier = -1;
  }
  if (sInput[0] == _T('0') && sInput[1] == _T('x')) {
    sInput += 2; uBase = 16;
  };
  return iSignMultiplier * String_2_ISAINT(sInput, NULL, uBase);
};

extern "C" {
  VOID __stdcall fCall(VOID*);
  VOID __stdcall fJump(VOID*);
  VOID __stdcall fIllegalInstruction();
  VOID __stdcall fIntergerOverflow();
  VOID __stdcall fPrivilegedInstruction();
}

// C++ exception
class cException: public std::exception {
} oException;

// cPureCallBase is initialize before initializing cPureCall. cPureCallBase call fVirtual,
// which has not been initialized, causing a pure vitual function call error.
class cPureCallBase;
VOID fCallVirtual (cPureCallBase* pBase);
class cPureCallBase {
  public:
    virtual void fVirtual() = 0;
	  cPureCallBase() { fCallVirtual(this); }
};
VOID fCallVirtual (cPureCallBase* pBase) {
  pBase->fVirtual();
}
class cPureCall : cPureCallBase {
  public:
     void fVirtual() {}
};
VOID fStackRecursion() {
  alloca(0x1000);
  fStackRecursion();
}
// Use globals to store some things, so these variables don't get overwritten when the stack is smashed
BYTE* gpAddress;
ISAUINT guCounter;
BOOL gbFreeHeap = FALSE;

UINT _tmain(UINT uArgumentsCount, _TCHAR* asArguments[]) {
  HANDLE hHeap = GetProcessHeap();
  _set_abort_behavior( 0, _WRITE_ABORT_MSG);
  if (uArgumentsCount < 2) {
    _tprintf(_T("Usage:\r\n"));
    _tprintf(_T("  %s exception [arguments]\r\n"), asArguments[0]);
    _tprintf(_T("Exceptions and arguments:\r\n"));
    _tprintf(_T("  Breakpoint\r\n"));
    _tprintf(_T("  CPUUsage\r\n"));
    _tprintf(_T("  IntegerDivideByZero\r\n"));
    _tprintf(_T("  IllegalInstruction\r\n"));
    _tprintf(_T("  PrivilegedInstruction\r\n"));
    _tprintf(_T("  PureCall\r\n"));
    _tprintf(_T("  StackExhaustion\r\n"));
    _tprintf(_T("  RecursiveCall\r\n"));
    _tprintf(_T("  C++\r\n"));
    _tprintf(_T("  OOM [HeapAlloc|C++] SIZE\r\n"));
    _tprintf(_T("    e.g. OOM HeapAlloc 0xC0000000\r\n"));
    _tprintf(_T("  Numbered NUMBER FLAGS\r\n"));
    _tprintf(_T("    e.g. Numbered 0x41414141 0x42424242\r\n"));
    _tprintf(_T("  AccessViolation [Call|Jmp|Read|Write] ADDRESS\r\n"));
    _tprintf(_T("    e.g. AccessViolation Call 0xDEADBEEF\r\n"));
    _tprintf(_T("         (attempt to execute code at address 0xDEADBEEF using a CALL instruction)\r\n"));
    _tprintf(_T("  UseAfterFree [Read|Write] SIZE OFFSET\r\n"));
    _tprintf(_T("    e.g. UseAfterFree Read 0x20 4\r\n"));
    _tprintf(_T("         (free a 0x20 byte heap buffer and read from offset 4 of the free memory)\r\n"));
    _tprintf(_T("  DoubleFree SIZE\r\n"));
    _tprintf(_T("    e.g. DoubleFree 0x20\r\n"));
    _tprintf(_T("         (free a 0x20 byte heap buffer twice)\r\n"));
    _tprintf(_T("  MisalignedFree SIZE OFFSET\r\n"));
    _tprintf(_T("    e.g. MisalignedFree 0x20 8\r\n"));
    _tprintf(_T("         (free a 0x20 byte heap buffer at offset 0x8)\r\n"));
    _tprintf(_T("  OutOfBounds [Heap|Stack] [Read|Write] SIZE OFFSET\r\n"));
    _tprintf(_T("    e.g. OutOfBounds Heap Read 0x20 1\r\n"));
    _tprintf(_T("         (read from an address 1 byte past the end of a 0x20 byte heap buffer)\r\n"));
    _tprintf(_T("    -or- OutOfBounds Stack Write 0x20 4\r\n"));
    _tprintf(_T("         (write to an address 4 bytes past the end of a 0x20 byte stack buffer)\r\n"));
    _tprintf(_T("  BufferOverrun [Heap|Stack] [Read|Write] SIZE OVERRUN\r\n"));
    _tprintf(_T("    e.g. BufferOverrun Heap Read 0x20 4\r\n"));
    _tprintf(_T("         (read 4 bytes past the end of a 0x20 byte heap buffer)\r\n"));
    _tprintf(_T("    -or- BufferOverrun Stack Write 0x30 1\r\n"));
    _tprintf(_T("         (read 1 byte past the end of a 0x30 byte stack buffer)\r\n"));
    _tprintf(_T("  BufferUnderrun [Heap|Stack] [Read|Write] SIZE UNDERRUN\r\n"));
    _tprintf(_T("    e.g. BufferUnderrun Heap Write 0x20 4\r\n"));
    _tprintf(_T("         (read 4 bytes before the start of a 0x20 byte heap buffer)\r\n"));
    _tprintf(_T("    -or- BufferUnderrun Stack Write 0x30 1\r\n"));
    _tprintf(_T("         (read 1 byte before the start of a 0x30 byte stack buffer)\r\n"));
  } else if (_tcsicmp(asArguments[1], _T("Nop")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Exiting cleanly...\r\n"));
  } else if (_tcsicmp(asArguments[1], _T("Breakpoint")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Triggering debug breakpoint...\r\n"));
    __debugbreak();
  } else if (_tcsicmp(asArguments[1], _T("CPUUsage")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Using 100% CPU in 1 thread...\r\n"));
    while(1){};
  } else if (_tcsicmp(asArguments[1], _T("IntegerDivideByZero")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Dividing by zero...\r\n"));
    volatile UINT uN = 0;
    uN = 0 / uN;
  } else if (_tcsicmp(asArguments[1], _T("IllegalInstruction")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Executing illegal instruction...\r\n"));
    fIllegalInstruction();
  } else if (_tcsicmp(asArguments[1], _T("PrivilegedInstruction")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Executing privileged instruction...\r\n"));
    fPrivilegedInstruction();
  } else if (_tcsicmp(asArguments[1], _T("PureCall")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Triggering pure virtual function call...\r\n"));
    cPureCall oPureCall;
  } else if (_tcsicmp(asArguments[1], _T("StackExhaustion")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 3) {
      _ftprintf(stderr, _T("Please provide a UINT memory block size to allocate for each stack chunk.\r\n"));
      return 1;
    };
    ISAUINT uChunkSize = fuParseNumber(asArguments[2]);
    while (1) {
      _ftprintf(stderr, _T("Allocating %d/0x%IX bytes of stack memory...\r\n"), uChunkSize, uChunkSize);
      alloca(uChunkSize);
    };
  } else if (_tcsicmp(asArguments[1], _T("RecursiveCall")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Calling function recursively...\r\n"));
    fStackRecursion();
  } else if (_tcsicmp(asArguments[1], _T("C++")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Throwing C++ exception...\r\n"));
    throw oException;
  } else if (_tcsicmp(asArguments[1], _T("OOM")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please provide a way of allocating memory (HeapAlloc or C++) and a UINT memory block size to allocate for each heap block.\r\n"));
      return 1;
    };
    BOOL bHeapAlloc = FALSE;
    if (_tcsicmp(asArguments[2], _T("HeapAlloc")) == 0) {
      bHeapAlloc = TRUE;
    } else if (_tcsicmp(asArguments[2], _T("C++")) != 0) {
      _ftprintf(stderr, _T("Please use HeapAlloc or C++, not %s\r\n"), asArguments[2]);
      return 1;
    };
    ISAUINT uBlockSize = fuParseNumber(asArguments[3]);
    while (1) {
      if (bHeapAlloc) {
        _ftprintf(stderr, _T("Allocating %d/0x%IX bytes of heap memory using HeapAlloc...\r\n"), uBlockSize, uBlockSize);
        BYTE* pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uBlockSize);
      } else {
        _ftprintf(stderr, _T("Allocating %d/0x%IX bytes of heap memory using new BYTE[]...\r\n"), uBlockSize, uBlockSize);
        BYTE* pMemory = new BYTE[uBlockSize];
      };
    };
  } else if (_tcsicmp(asArguments[1], _T("Numbered")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please provide a DWORD code and DWORD flags for the exception.\r\n"));
      return 1;
    };
    DWORD dwCode = fdwParseDWORD(asArguments[2]);
    DWORD dwFlags = fdwParseDWORD(asArguments[3]);
    // TODO: implement arguments?
    RaiseException(dwCode, dwFlags, 0, NULL);
  } else if (_tcsicmp(asArguments[1], _T("AccessViolation")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please provide an access type (call, jump, read, write) and a UINT address to access.\r\n"));
      return 1;
    };
    VOID* pAddress = fpParsePointer(asArguments[3]);
    if (_tcsicmp(asArguments[2], _T("Call")) == 0) {
      _ftprintf(stderr, _T("Calling address 0x%p...\r\n"), pAddress);
      fCall(pAddress);
    } else if (_tcsicmp(asArguments[2], _T("Jump")) == 0) {
      _ftprintf(stderr, _T("Jumping to address 0x%p...\r\n"), pAddress);
      fJump(pAddress);
    } else if (_tcsicmp(asArguments[2], _T("Read")) == 0) {
      _ftprintf(stderr, _T("Reading from address 0x%p...\r\n"), pAddress);
      BYTE x = *(BYTE*)pAddress;
      _ftprintf(stderr, _T("Writing to address 0x%p...\r\n"), pAddress);
    } else if (_tcsicmp(asArguments[2], _T("Write")) == 0) {
      *(BYTE*)pAddress = BYTE_TO_WRITE;
    } else {
      _ftprintf(stderr, _T("Please use Call, Jmp, Read or Write, not %s\r\n"), asArguments[2]);
      return 1;
    };
  } else if (_tcsicmp(asArguments[1], _T("UseAfterFree")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 5) {
      _ftprintf(stderr, _T("Please provide a type of access (read, write), a UINT memory block size and an INT offset at which to access it.\r\n"));
      return 1;
    };
    ISAUINT uSize = fuParseNumber(asArguments[3]);
    ISAINT iOffset = fiParseNumber(asArguments[4]);
    BYTE* pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uSize);
    HeapFree(hHeap, 0, pMemory);
    if (_tcsicmp(asArguments[2], _T("Read")) == 0) {
      _ftprintf(stderr, _T("Reading at offset %d/0x%IX from a %d/0x%IX byte freed heap memory block at 0x%p...\r\n"),
          iOffset, iOffset, uSize, uSize, pMemory);
      BYTE x = *(pMemory + iOffset);
    } else if (_tcsicmp(asArguments[2], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing at offset %d/0x%IX to a %d/0x%IX byte freed heap memory block at 0x%p...\r\n"),
          iOffset, iOffset, uSize, uSize, pMemory);
      *(pMemory + iOffset) = BYTE_TO_WRITE;
    } else {
      _ftprintf(stderr, _T("Please use Read or Write, not %s\r\n"), asArguments[2]);
      return 1;
    }
  } else if (_tcsicmp(asArguments[1], _T("DoubleFree")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 3) {
      _ftprintf(stderr, _T("Please provide a UINT memory block size.\r\n"));
      return 1;
    };
    ISAUINT uMemoryBlockSize = fuParseNumber(asArguments[2]);
    BYTE* pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uMemoryBlockSize);
    HeapFree(hHeap, 0, (PVOID)pMemory);
    _ftprintf(stderr, _T("Freeing a %d/0x%IX byte freed heap memory block twice at 0x%p...\r\n"),
        uMemoryBlockSize, uMemoryBlockSize, pMemory);
    HeapFree(hHeap, 0, (PVOID)pMemory);
  } else if (_tcsicmp(asArguments[1], _T("MisalignedFree")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please provide a UINT memory block size and an INT offset at which to free it.\r\n"));
      return 1;
    };
    ISAUINT uMemoryBlockSize = fuParseNumber(asArguments[2]);
    ISAINT iOffset = fiParseNumber(asArguments[3]);
    BYTE* pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uMemoryBlockSize);
    _ftprintf(stderr, _T("Freeing offset %d/0x%IX of a %d/0x%IX byte heap memory block at 0x%p...\r\n"),
        iOffset, iOffset, uMemoryBlockSize, uMemoryBlockSize, pMemory);
    HeapFree(hHeap, 0, (PVOID)(pMemory + iOffset));
  } else if (_tcsicmp(asArguments[1], _T("OutOfBounds")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 6) {
      _ftprintf(stderr, _T("Please provide type of memory (heap, stack), a type of access (read, write), a UINT memory block size, an INT offset at which to access it, and optionally a UINT number of bytes to access.\r\n"));
      return 1;
    };
    ISAUINT uMemoryBlockSize = fuParseNumber(asArguments[4]);
    ISAINT iOffset = fiParseNumber(asArguments[5]);
    ISAUINT uAccessSize = uArgumentsCount < 7 ? 0 : fuParseNumber(asArguments[6]);
    BYTE* pMemory;
    _TCHAR* sMemoryType = NULL;
    if (_tcsicmp(asArguments[2], _T("Heap")) == 0) {
      pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uMemoryBlockSize);
      sMemoryType = _T("heap");
      gbFreeHeap = TRUE;
    } else if (_tcsicmp(asArguments[2], _T("Stack")) == 0) {
      pMemory = (BYTE*)alloca(uMemoryBlockSize);
      sMemoryType = _T("stack");
    } else {
      _ftprintf(stderr, _T("Please use Heap or Stack, not %s\r\n"), asArguments[2]);
      return 1;
    }
    if (_tcsicmp(asArguments[3], _T("Read")) == 0) {
      _ftprintf(stderr, _T("Reading at offset %d/0x%IX from a %d/0x%IX byte %s memory block at 0x%p...\r\n"),
          iOffset, iOffset, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (BYTE* pAddress = pMemory + iOffset; pAddress < pMemory + iOffset + uAccessSize; pAddress++) {
        BYTE x = *pAddress;
      };
    } else if (_tcsicmp(asArguments[3], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing at offset %d/0x%IX to a %d/0x%IX byte %s memory block at 0x%p...\r\n"),
          iOffset, iOffset, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (gpAddress = pMemory + iOffset, guCounter = uAccessSize; guCounter--; gpAddress++) {
        *gpAddress = BYTE_TO_WRITE;
      };
    } else {
      _ftprintf(stderr, _T("Please use Read or Write, not %s\r\n"), asArguments[3]);
      return 1;
    }
    if (gbFreeHeap) {
      HeapFree(hHeap, 0, pMemory);
    };
  } else if (_tcsicmp(asArguments[1], _T("BufferOverrun")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 6) {
      _ftprintf(stderr, _T("Please provide type of memory (heap, stack), a type of access (read, write), a UINT memory block size, and a UINT number of bytes to overrun it.\r\n"));
      return 1;
    };
    ISAUINT uMemoryBlockSize = fuParseNumber(asArguments[4]);
    ISAUINT uOverrunSize = fuParseNumber(asArguments[5]);
    BYTE* pMemory;
    _TCHAR* sMemoryType = NULL;
    if (_tcsicmp(asArguments[2], _T("Heap")) == 0) {
      pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uMemoryBlockSize);
      sMemoryType = _T("heap");
      gbFreeHeap = TRUE;
    } else if (_tcsicmp(asArguments[2], _T("Stack")) == 0) {
      pMemory = (BYTE*)alloca(uMemoryBlockSize);
      sMemoryType = _T("stack");
    } else {
      _ftprintf(stderr, _T("Please use Heap or Stack, not %s\r\n"), asArguments[2]);
      return 1;
    }
    if (_tcsicmp(asArguments[3], _T("Read")) == 0) {
      _ftprintf(stderr, _T("Reading %d/0x%IX bytes beyond a %d/0x%IX byte %s memory block at 0x%p...\r\n"),
          uOverrunSize, uOverrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (BYTE* pAddress = pMemory; pAddress < pMemory + uMemoryBlockSize + uOverrunSize; pAddress++) {
        BYTE x = *pAddress;
      };
    } else if (_tcsicmp(asArguments[3], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing %d/0x%IX bytes beyond a %d/0x%IX byte %s memory block at 0x%p...\r\n"),
          uOverrunSize, uOverrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (gpAddress = pMemory + uMemoryBlockSize, guCounter = uOverrunSize; guCounter--; gpAddress++) {
        *gpAddress = BYTE_TO_WRITE;
      };
    } else {
      _ftprintf(stderr, _T("Please use Read or Write, not %s\r\n"), asArguments[3]);
      return 1;
    }
    if (gbFreeHeap) {
      HeapFree(hHeap, 0, pMemory);
    };
  } else if (_tcsicmp(asArguments[1], _T("BufferUnderrun")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 6) {
      _ftprintf(stderr, _T("Please provide type of memory (heap, stack), a type of access (read, write), a UINT memory block size, and a UINT number of bytes to underrun it.\r\n"));
      return 1;
    };
    ISAUINT uMemoryBlockSize = fuParseNumber(asArguments[4]);
    ISAUINT uUnderrunSize = fuParseNumber(asArguments[5]);
    BYTE* pMemory;
    _TCHAR* sMemoryType = NULL;
    if (_tcsicmp(asArguments[2], _T("Heap")) == 0) {
      pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uMemoryBlockSize);
      sMemoryType = _T("heap");
      gbFreeHeap = TRUE;
    } else if (_tcsicmp(asArguments[2], _T("Stack")) == 0) {
      pMemory = (BYTE*)alloca(uMemoryBlockSize);
      sMemoryType = _T("stack");
    } else {
      _ftprintf(stderr, _T("Please use Heap or Stack, not %s\r\n"), asArguments[2]);
      return 1;
    }
    if (_tcsicmp(asArguments[3], _T("Read")) == 0) {
      _ftprintf(stderr, _T("Reading %d/0x%IX bytes before a %d/0x%IX byte %s memory block at 0x%p...\r\n"),
          uUnderrunSize, uUnderrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (BYTE* pAddress = pMemory; pAddress >= pMemory - uUnderrunSize; pAddress--) {
        BYTE x = *pAddress;
      };
    } else if (_tcsicmp(asArguments[3], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing %d/0x%IX bytes before a %d/0x%IX byte %s memory block at 0x%p...\r\n"),
          uUnderrunSize, uUnderrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (gpAddress = pMemory, guCounter = uUnderrunSize; guCounter--; gpAddress--) {
        *gpAddress = BYTE_TO_WRITE;
      };
    } else {
      _ftprintf(stderr, _T("Please use Read or Write, not %s\r\n"), asArguments[3]);
      return 1;
    }
    if (gbFreeHeap) {
      HeapFree(hHeap, 0, pMemory);
    };
  } else {
    _ftprintf(stderr, _T("Invalid test type %s\r\n"), asArguments[1]);
    return 1;
  }
  return 0;
}
