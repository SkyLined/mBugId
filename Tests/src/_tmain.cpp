#include <exception>
#include <limits.h>
#include <new>
#include <Roerrorapi.h>
#include <safeint.h>
#include <SDKDDKVer.h>
#include <stdio.h>
#include <tchar.h>
#include <windows.h>
#include <Winstring.h>

// Use Instruction Set Architecture (ISA) specific (unsigned) integers:
#ifdef _WIN64
  #define ISAINT signed __int64
  #define ISAUINT unsigned __int64
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
  INT iBase = 10;
  if (sInput[0] == _T('0') && sInput[1] == _T('x')) {
    sInput += 2; iBase = 16;
  };
  return (DWORD)_tcstoul(sInput, NULL, iBase);
};
ISAUINT fuParseNumber(_TCHAR* sInput) {
  INT iBase = 10;
  if (sInput[0] == _T('0') && sInput[1] == _T('x')) {
    sInput += 2; iBase = 16;
  };
  return String_2_ISAUINT(sInput, NULL, iBase);
};
ISAINT fiParseNumber(_TCHAR* sInput) {
  INT iBase = 10;
  BOOL bNegative = FALSE;
  if (sInput[0] == _T('-')) {
    sInput += 1; bNegative = TRUE;
  }
  if (sInput[0] == _T('0') && sInput[1] == _T('x')) {
    sInput += 2; iBase = 16;
  };
  ISAINT iNumber = String_2_ISAINT(sInput, NULL, iBase);
  if (bNegative) {
    iNumber = -iNumber;
  };
  return iNumber;
};
BYTE fuReadByte(PVOID pAddress) {
  return *(PBYTE)pAddress;
};
BYTE fuReadByte(PBYTE pAddress) {
  return *pAddress;
};
#define BYTE_TO_WRITE 0x41
VOID fWriteByte(PVOID pAddress) {
  *(PBYTE)pAddress = BYTE_TO_WRITE;
};
VOID fWriteByte(PBYTE pAddress) {
  *pAddress = BYTE_TO_WRITE;
};

extern "C" {
  VOID __stdcall fCall(VOID*);
  VOID __stdcall fJump(VOID*);
  VOID __stdcall fIllegalInstruction(VOID*);
  VOID __stdcall fIntegerOverflow(VOID*);
  VOID __stdcall fPrivilegedInstruction(VOID*);
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

// For use with WRTLanguage errors
class cIUnknown : IUnknown {
  private:
    ULONG uRefCounter;
  public:
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, PVOID* ppv) {
      if (ppv == NULL) return E_INVALIDARG;
      *ppv = NULL;
      if (riid != IID_IUnknown) {
        GUID guid = (GUID)riid;
        _tprintf(_T("Cannot instantiate %08X-%04X-%04X-%02X%02X-%02X%02X%02X%02X%02X%02X\r\n"),
            (UINT)guid.Data1,
            (WORD)guid.Data2,
            (WORD)guid.Data3,
            (BYTE)guid.Data4[0],
            (BYTE)guid.Data4[1],
            (BYTE)guid.Data4[2],
            (BYTE)guid.Data4[3],
            (BYTE)guid.Data4[4],
            (BYTE)guid.Data4[5],
            (BYTE)guid.Data4[6],
            (BYTE)guid.Data4[7]
         );
        return E_NOINTERFACE;
      }
      _tprintf(_T("OK\r\n"));
      *ppv = (PVOID)this; 
      AddRef(); 
      return NO_ERROR;
    };
    ULONG STDMETHODCALLTYPE AddRef() {
      return ++uRefCounter;
    };
    ULONG STDMETHODCALLTYPE Release() {
      ULONG uResult = --uRefCounter;
      if (uResult == 0) delete this;
      return uResult;
    };
};

VOID fStackRecursionFunction1(ISAUINT);
VOID fStackRecursionFunction2(ISAUINT);
ISAUINT guStackRecursionCounter = 0;

VOID fStackRecursion(ISAUINT uFunctionsInLoop) {
  fStackRecursionFunction1(uFunctionsInLoop);
};
VOID fStackRecursionFunction1(ISAUINT uFunctionsInLoop) {
  alloca(0x1000);
  guStackRecursionCounter++;
  if (uFunctionsInLoop > 1 && guStackRecursionCounter % uFunctionsInLoop == 0) {
    fStackRecursionFunction2(uFunctionsInLoop);
  } else {
    fStackRecursionFunction1(uFunctionsInLoop);
  };
};
VOID fStackRecursionFunction2(ISAUINT uFunctionsInLoop) {
  alloca(0x1000);
  guStackRecursionCounter++;
  fStackRecursionFunction1(uFunctionsInLoop);
};

// Use globals to store some things, so these variables don't get overwritten when the stack is smashed
BYTE* gpAddress;
ISAUINT guCounter;
BOOL gbFreeHeap = FALSE;

UINT _tmain(UINT uArgumentsCount, _TCHAR* asArguments[]) {
  // disable buffering
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);
  HANDLE hHeap = GetProcessHeap();
  _set_abort_behavior( 0, _WRITE_ABORT_MSG);
  if (
    uArgumentsCount < 2
    || _tcsicmp(asArguments[1], _T("-h")) == 0
    || _tcsicmp(asArguments[1], _T("-?")) == 0
    || _tcsicmp(asArguments[1], _T("/h")) == 0
    || _tcsicmp(asArguments[1], _T("/?")) == 0
    || _tcsicmp(asArguments[1], _T("--help")) == 0
  ) {
    _tprintf(_T("Usage:\r\n"));
    _tprintf(_T("  %s exception [arguments]\r\n"), asArguments[0]);
    _tprintf(_T("Exceptions and arguments:\r\n"));
                 ////////////////////////////////////////////////////////////////////////////////
    _tprintf(_T("  Breakpoint\r\n"));
    _tprintf(_T("  CPUUsage\r\n"));
    _tprintf(_T("  IntegerDivideByZero\r\n"));
    _tprintf(_T("  IntegerOverflow\r\n"));
    _tprintf(_T("  IllegalInstruction\r\n"));
    _tprintf(_T("  PrivilegedInstruction\r\n"));
    _tprintf(_T("  PureCall\r\n"));
    _tprintf(_T("  StackExhaustion SIZE\r\n"));
    _tprintf(_T("    e.g. StackExhaustion 0x000F0000\r\n"));
    _tprintf(_T("         (repeatedly attempt to allocate 0xF0000 bytes of stack memory until a\r\n"));
    _tprintf(_T("         stack exhaustion exception crashes the application).\r\n"));
    _tprintf(_T("  RecursiveCall NUMBER_OF_FUNCTIONS_IN_LOOP\r\n"));
    _tprintf(_T("    e.g. RecursiveCall 5\r\n"));
    _tprintf(_T("         (Recursively call two different functions, where one is called once\r\n"));
    _tprintf(_T("         every five calls and the other four times, creating a loop of five\r\n"));
    _tprintf(_T("         calls total.)\r\n"));
    _tprintf(_T("  C++\r\n"));
    _tprintf(_T("  WRTLanguage HRESULT MESSAGE\r\n"));
    _tprintf(_T("    e.g. WRTLanguage 0x87654321 \"Windows Run-Time Originate Language error\"\r\n"));
    _tprintf(_T("  WRTOriginate HRESULT MESSAGE\r\n"));
    _tprintf(_T("    e.g. WRTOriginate 0x87654321 \"Windows Run-Time Originate error\"\r\n"));
    _tprintf(_T("  OOM [HeapAlloc|C++|Stack] SIZE\r\n"));
    _tprintf(_T("    e.g. OOM HeapAlloc 0x000F0000\r\n"));
    _tprintf(_T("         (repeatedly attempt to allocate 0xF0000 bytes of memory until an\r\n"));
    _tprintf(_T("         out-of-memory exception crashes the application)\r\n"));
    _tprintf(_T("    -or- OOM Stack 0x000F0000\r\n"));
    _tprintf(_T("         (repeatedly use HeapAlloc to allocate 0xF0000 bytes of memory until\r\n"));
    _tprintf(_T("          all available memory is consumed, then repeatedly attempt to allocate\r\n"));
    _tprintf(_T("          0xF0000 bytes of stack memory until a stack exhaustion exception\r\n"));
    _tprintf(_T("          crashes the application).\r\n"));
    _tprintf(_T("  Numbered NUMBER FLAGS\r\n"));
    _tprintf(_T("    e.g. Numbered 0x41414141 0x42424242\r\n"));
    _tprintf(_T("  AccessViolation [Call|Jmp|Read|Write] ( ADDRESS | TYPE )\r\n"));
    _tprintf(_T("         TYPE can be any of \"Unallocated\", \"Reserved\", \"NoAccess\", or \"Guard\".\r\n"));
    _tprintf(_T("         If a TYPE keyword is specified, the code creates a memory region of that\r\n"));
    _tprintf(_T("         type and uses its address instead of a user supplied address.\r\n"));
    _tprintf(_T("    e.g. AccessViolation Call 0xDEADBEEF\r\n"));
    _tprintf(_T("         (attempt to execute code at address 0xDEADBEEF using a CALL instruction)\r\n"));
    _tprintf(_T("    e.g. AccessViolation Read Unallocated\r\n"));
    _tprintf(_T("         (attempt to read from unallocated memory)\r\n"));
    _tprintf(_T("  UseAfterFree [Call|Jmp|Read|Write] SIZE OFFSET\r\n"));
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
    _tprintf(_T("  WrongHeapHandle SIZE\r\n"));
    _tprintf(_T("    e.g. WrongHeapHandle 0x20\r\n"));
    _tprintf(_T("         (allocate 0x20 bytes on one heap, then attempt to free it on another)\r\n"));
    _tprintf(_T("  SafeInt ...\r\n"));
  } else if (_tcsicmp(asArguments[1], _T("Nop")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Exiting cleanly...\r\n"));
  } else if (_tcsicmp(asArguments[1], _T("Breakpoint")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Triggering debug breakpoint...\r\n"));
    __debugbreak();
  } else if (_tcsicmp(asArguments[1], _T("CPUUsage")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Using 100%% CPU in 1 thread...\r\n"));
    while(1){};
  } else if (_tcsicmp(asArguments[1], _T("IntegerDivideByZero")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Dividing by zero...\r\n"));
    volatile UINT uN = 0;
    uN = 0 / uN;
  } else if (_tcsicmp(asArguments[1], _T("IntegerOverflow")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Triggering integer overflow...\r\n"));
    fIntegerOverflow(NULL);
  } else if (_tcsicmp(asArguments[1], _T("IllegalInstruction")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Executing illegal instruction...\r\n"));
    fIllegalInstruction(NULL);
  } else if (_tcsicmp(asArguments[1], _T("PrivilegedInstruction")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Executing privileged instruction...\r\n"));
    fPrivilegedInstruction(NULL);
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
    ISAUINT uBlockSize = fuParseNumber(asArguments[2]);
    _ftprintf(stderr, _T("Repeatedly allocating %Id/0x%IX bytes of stack memory...\r\n"), uBlockSize, uBlockSize);
    while (1) alloca(uBlockSize);
  } else if (_tcsicmp(asArguments[1], _T("RecursiveCall")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 3) {
      _ftprintf(stderr, _T("Please provide a UINT number of calls in the cursion loop.\r\n"));
      return 1;
    };
    ISAUINT uFunctionsInLoop = fuParseNumber(asArguments[2]);
    _ftprintf(stderr, _T("Calling %Id functions recursively...\r\n"), uFunctionsInLoop);
    fStackRecursion(uFunctionsInLoop);
  } else if (_tcsicmp(asArguments[1], _T("C++")) == 0) {
    /*                                                                        */
    _ftprintf(stderr, _T("Throwing C++ exception...\r\n"));
    throw oException;
  } else if (_tcsicmp(asArguments[1], _T("FailFast")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please provide ExceptionCode and ExceptionAddress values.\r\n"));
      return 1;
    };
    EXCEPTION_RECORD oExceptionRecord = {
      (DWORD)fuParseNumber(asArguments[2]), // ExceptionCode
      EXCEPTION_NONCONTINUABLE, // ExceptionFlags
      NULL, // ExceptionRecord
      (PVOID)fuParseNumber(asArguments[3]), // ExceptionAddress
      0, // NumberParameters
      {0}, // ExceptionInformation
    };
    RaiseFailFastException(&oExceptionRecord, NULL, 0);
  } else if (_tcsicmp(asArguments[1], _T("WRTOriginate")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please a HRESULT value and a message string.\r\n"));
      return 1;
    };
    HSTRING hString;
    HSTRING_HEADER hStringHeader;
    HRESULT hResult = CoInitialize(NULL);
    if (!SUCCEEDED(hResult)) {
      _ftprintf(stderr, _T("CoInitialize call failed.\r\n"));
      return 1;
    };
    hResult = WindowsCreateStringReference(asArguments[3], _tcslen(asArguments[3]), &hStringHeader, &hString);
    if (!SUCCEEDED(hResult)) {
      _ftprintf(stderr, _T("WindowsCreateStringReference call failed.\r\n"));
      return 1;
    };
    hResult = (HRESULT)fuParseNumber(asArguments[2]);
    if (SUCCEEDED(hResult)) {
      _ftprintf(stderr, _T("HRESULT %lX is a success code.\r\n"), hResult);
      return 1;
    };
    _ftprintf(stderr, _T("Creating Originate Error(%lX, %s)...\r\n"), hResult, asArguments[3]);
    if (!RoOriginateError(hResult, hString)) {
      _ftprintf(stderr, _T("RoOriginateError call failed.\r\n"));
      return 1;
    };
    _ftprintf(stderr, _T("Capturing Error Context...\r\n"));
    if (!SUCCEEDED(RoCaptureErrorContext(hResult))) {
      _ftprintf(stderr, _T("RoCaptureErrorContext call failed.\r\n"));
      return 1;
    };
    _ftprintf(stderr, _T("Throwing FailFast exception...\r\n"));
    RoFailFastWithErrorContext(hResult);
  } else if (_tcsicmp(asArguments[1], _T("WRTLanguage")) == 0) {
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please a HRESULT value and a message string.\r\n"));
      return 1;
    };
    HSTRING hString;
    HSTRING_HEADER hStringHeader;
    HRESULT hResult = CoInitialize(NULL);
    if (!SUCCEEDED(hResult)) {
      _ftprintf(stderr, _T("CoInitialize call failed.\r\n"));
      return 1;
    };
    hResult = WindowsCreateStringReference(asArguments[3], _tcslen(asArguments[3]), &hStringHeader, &hString);
    if (!SUCCEEDED(hResult)) {
      _ftprintf(stderr, _T("WindowsCreateStringReference call failed.\r\n"));
      return 1;
    };
    hResult = (HRESULT)fuParseNumber(asArguments[2]);
    if (SUCCEEDED(hResult)) {
      _ftprintf(stderr, _T("HRESULT %lX is a success code.\r\n"), hResult);
      return 1;
    };
    IUnknown* pIUnknown = (IUnknown*)new cIUnknown();
    _ftprintf(stderr, _T("Creating Originate Language Error(%lX, %s, %p)...\r\n"), hResult, asArguments[3], pIUnknown);
    if (!RoOriginateLanguageException(hResult, hString, pIUnknown)) {
      _ftprintf(stderr, _T("RoOriginateLanguageException call failed.\r\n"));
      return 1;
    };
    _ftprintf(stderr, _T("Capturing Error Context...\r\n"));
    if (!SUCCEEDED(RoCaptureErrorContext(hResult))) {
      _ftprintf(stderr, _T("RoCaptureErrorContext call failed.\r\n"));
      return 1;
    };
    _ftprintf(stderr, _T("Throwing FailFast exception...\r\n"));
    RoFailFastWithErrorContext(hResult);
  } else if (_tcsicmp(asArguments[1], _T("OOM")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 4) {
      _ftprintf(stderr, _T("Please provide a way of allocating memory (HeapAlloc or C++) and a UINT memory block size to allocate for each heap block.\r\n"));
      return 1;
    };
    BOOL bHeapAlloc = FALSE, bCPP = FALSE, bStack = FALSE;
    if (_tcsicmp(asArguments[2], _T("HeapAlloc")) == 0) {
      bHeapAlloc = TRUE;
    } else if (_tcsicmp(asArguments[2], _T("C++")) == 0) {
      bCPP = TRUE;
    } else if (_tcsicmp(asArguments[2], _T("Stack")) == 0) {
      bStack = TRUE;
    } else {
      _ftprintf(stderr, _T("Please use HeapAlloc, C++ or Stack, not %s\r\n"), asArguments[2]);
      return 1;
    };
    ISAUINT uBlockSize = fuParseNumber(asArguments[3]);
    _ftprintf(stderr, _T("Repeatedly allocating %Id/0x%IX bytes of heap memory using %s...\r\n"), uBlockSize, uBlockSize, \
        bHeapAlloc ? _T("HeapAlloc") : bCPP ? _T("new BYTE[]") : _T("HeapAlloc to cause low memory"));
    while (1) {
      if (bHeapAlloc) {
        (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uBlockSize);
      } else if (bCPP) {
        new BYTE[uBlockSize];
      } else {
        BYTE* pMemory = (BYTE*)HeapAlloc(hHeap, 0, uBlockSize);
        if (pMemory == NULL) {
          _ftprintf(stderr, _T("Repeatedly allocating %Id/0x%IX bytes of stack memory...\r\n"), uBlockSize, uBlockSize);
          while (1) alloca(uBlockSize);
        };
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
    VOID* pAddress;
    if (_tcsicmp(asArguments[3], _T("Unallocated")) == 0) {
      pAddress = VirtualAlloc(NULL, 1, MEM_COMMIT, PAGE_NOACCESS);
      if (pAddress == NULL) {
        _ftprintf(stderr, _T("Cannot allocate memory.\r\n"));
        return 1;
      };
      if (!VirtualFree(pAddress, 0, MEM_RELEASE)) {
        _ftprintf(stderr, _T("Cannot free allocated memory.\r\n"));
        return 1;
      };
    } else if (_tcsicmp(asArguments[3], _T("Reserved")) == 0) {
      pAddress = VirtualAlloc(NULL, 1, MEM_RESERVE, PAGE_NOACCESS);
      if (pAddress == NULL) {
        _ftprintf(stderr, _T("Cannot reserve memory.\r\n"));
        return 1;
      };
    } else if (_tcsicmp(asArguments[3], _T("NoAccess")) == 0) {
      pAddress = VirtualAlloc(NULL, 1, MEM_COMMIT, PAGE_NOACCESS);
      if (pAddress == NULL) {
        _ftprintf(stderr, _T("Cannot allocate NoAccess memory.\r\n"));
        return 1;
      };
    } else if (_tcsicmp(asArguments[3], _T("Guard")) == 0) {
      pAddress = VirtualAlloc(NULL, 1, MEM_COMMIT, PAGE_EXECUTE_READWRITE | PAGE_GUARD);
      if (pAddress == NULL) {
        _ftprintf(stderr, _T("Cannot allocated guard page memory.\r\n"));
        return 1;
      };
    } else {
      pAddress = fpParsePointer(asArguments[3]);
    };
    if (_tcsicmp(asArguments[2], _T("Call")) == 0) {
      _ftprintf(stderr, _T("Calling address 0x%p...\r\n"), pAddress);
      fCall(pAddress);
    } else if (_tcsicmp(asArguments[2], _T("Jump")) == 0) {
      _ftprintf(stderr, _T("Jumping to address 0x%p...\r\n"), pAddress);
      fJump(pAddress);
    } else if (_tcsicmp(asArguments[2], _T("Read")) == 0) {
      _ftprintf(stderr, _T("Reading from address 0x%p...\r\n"), pAddress);
      fuReadByte(pAddress);
    } else if (_tcsicmp(asArguments[2], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing to address 0x%p...\r\n"), pAddress);
      fWriteByte(pAddress);
    } else {
      _ftprintf(stderr, _T("Please use Call, Jmp, Read, or Write, not %s\r\n"), asArguments[2]);
      return 1;
    };
  } else if (_tcsicmp(asArguments[1], _T("UseAfterFree")) == 0) {
    /*                                                                        */
    if (uArgumentsCount < 5) {
      _ftprintf(stderr, _T("Please provide a type of access (call, jmp, read, write), a UINT memory block size and an INT offset at which to access it.\r\n"));
      return 1;
    };
    ISAUINT uSize = fuParseNumber(asArguments[3]);
    ISAINT iOffset = fiParseNumber(asArguments[4]);
    BYTE* pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uSize);
    HeapFree(hHeap, 0, pMemory);
    if (_tcsicmp(asArguments[2], _T("Call")) == 0) {
      _ftprintf(stderr, _T("Calling offset %Id/0x%IX in a %Id/0x%IX byte freed heap memory block at 0x%p...\r\n"),
          iOffset, iOffset, uSize, uSize, pMemory);
      fCall(pMemory + iOffset);
    } else if (_tcsicmp(asArguments[2], _T("Jump")) == 0) {
      _ftprintf(stderr, _T("Jumping to offset %Id/0x%IX in a %Id/0x%IX byte freed heap memory block at 0x%p...\r\n"),
          iOffset, iOffset, uSize, uSize, pMemory);
      fJump(pMemory + iOffset);
    } else if (_tcsicmp(asArguments[2], _T("Read")) == 0) {
      _ftprintf(stderr, _T("Reading at offset %Id/0x%IX from a %Id/0x%IX byte freed heap memory block at 0x%p...\r\n"),
          iOffset, iOffset, uSize, uSize, pMemory);
      fuReadByte(pMemory + iOffset);
    } else if (_tcsicmp(asArguments[2], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing at offset %Id/0x%IX to a %Id/0x%IX byte freed heap memory block at 0x%p...\r\n"),
          iOffset, iOffset, uSize, uSize, pMemory);
      fWriteByte(pMemory + iOffset);
    } else {
      _ftprintf(stderr, _T("Please use Call, Jmp, Read, or Write, not %s\r\n"), asArguments[2]);
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
    _ftprintf(stderr, _T("Freeing a %Id/0x%IX byte freed heap memory block twice at 0x%p...\r\n"),
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
    _ftprintf(stderr, _T("Freeing offset %Id/0x%IX of a %Id/0x%IX byte heap memory block at 0x%p...\r\n"),
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
      _ftprintf(stderr, _T("Reading at offset %Id/0x%IX from a %Id/0x%IX byte %s memory block at 0x%p...\r\n"),
          iOffset, iOffset, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (BYTE* pAddress = pMemory + iOffset; pAddress < pMemory + iOffset + uAccessSize; pAddress++) {
        fuReadByte(pAddress);
      };
    } else if (_tcsicmp(asArguments[3], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing at offset %Id/0x%IX to a %Id/0x%IX byte %s memory block at 0x%p...\r\n"),
          iOffset, iOffset, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (gpAddress = pMemory + iOffset, guCounter = uAccessSize; guCounter--; gpAddress++) {
        fWriteByte(gpAddress);
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
      _ftprintf(stderr, _T("Reading %Id/0x%IX bytes beyond a %Id/0x%IX byte %s memory block at 0x%p...\r\n"),
          uOverrunSize, uOverrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (BYTE* pAddress = pMemory; pAddress < pMemory + uMemoryBlockSize + uOverrunSize; pAddress++) {
        fuReadByte(pAddress);
      };
    } else if (_tcsicmp(asArguments[3], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing %Id/0x%IX bytes beyond a %Id/0x%IX byte %s memory block at 0x%p...\r\n"),
          uOverrunSize, uOverrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (gpAddress = pMemory + uMemoryBlockSize, guCounter = uOverrunSize; guCounter--; gpAddress++) {
        fWriteByte(gpAddress);
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
      _ftprintf(stderr, _T("Reading %Id/0x%IX bytes before a %Id/0x%IX byte %s memory block at 0x%p...\r\n"),
          uUnderrunSize, uUnderrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (BYTE* pAddress = pMemory; pAddress >= pMemory - uUnderrunSize; pAddress--) {
        fuReadByte(pAddress);
      };
    } else if (_tcsicmp(asArguments[3], _T("Write")) == 0) {
      _ftprintf(stderr, _T("Writing %Id/0x%IX bytes before a %Id/0x%IX byte %s memory block at 0x%p...\r\n"),
          uUnderrunSize, uUnderrunSize, uMemoryBlockSize, uMemoryBlockSize, sMemoryType, pMemory);
      for (gpAddress = pMemory, guCounter = uUnderrunSize; guCounter--; gpAddress--) {
        fWriteByte(gpAddress);
      };
    } else {
      _ftprintf(stderr, _T("Please use Read or Write, not %s\r\n"), asArguments[3]);
      return 1;
    }
    if (gbFreeHeap) {
      HeapFree(hHeap, 0, pMemory);
    };
  } else if (_tcsicmp(asArguments[1], _T("WrongHeapHandle")) == 0) {
    //--------------------------------------------------------------------------
    // Allocate memory on the heap, then create a second heap and use it to try
    // to free the memory.
    if (uArgumentsCount < 3) {
      _ftprintf(stderr, _T("Please provide a UINT memory block size.\r\n"));
      return 1;
    };
    ISAUINT uMemoryBlockSize = fuParseNumber(asArguments[2]);
    BYTE* pMemory = (BYTE*)HeapAlloc(hHeap, HEAP_GENERATE_EXCEPTIONS, uMemoryBlockSize);
    HANDLE hSecondHeap = HeapCreate(
      0, // DWORD  flOptions
      0, // SIZE_T dwInitialSize,
      0 // SIZE_T dwMaximumSize
    );
    _ftprintf(stderr, _T("Freeing a %Id/0x%IX byte heap memory block at 0x%p from heap 0x%p using heap 0x%p...\r\n"),
        uMemoryBlockSize, uMemoryBlockSize, pMemory, hHeap, hSecondHeap);
    HeapFree(hSecondHeap, 0, pMemory);
  } else if (_tcsicmp(asArguments[1], _T("SafeInt")) == 0) {
    //--------------------------------------------------------------------------
    if (uArgumentsCount < 5) {
      _ftprintf(stderr, _T("Please provide an invalid integer operation to perform (++, --, *, truncate, signedness), a type (signed, unsigned) and bit size (8, 16, 32, or 64).\r\n"));
      return 1;
    };
    BOOL bIncrease = _tcsicmp(asArguments[2], _T("++")) == 0;
    BOOL bDecrease = !bIncrease && _tcsicmp(asArguments[2], _T("--")) == 0;
    BOOL bMultiply = !bIncrease && !bDecrease && _tcsicmp(asArguments[2], _T("*")) == 0;
    BOOL bTruncate = !bIncrease && !bDecrease && !bMultiply && _tcsicmp(asArguments[2], _T("truncate")) == 0;
    BOOL bSignedness = !bIncrease && !bDecrease && !bMultiply && !bTruncate;
    if (bSignedness && !_tcsicmp(asArguments[2], _T("signedness")) == 0) {
      _ftprintf(stderr, _T("Please provide an invalid integer operation to perform (++, --, truncate, signedness), not %s.\r\n"), asArguments[1]);
      return 1;
    };
    BOOL bSigned = _tcsicmp(asArguments[3], _T("signed")) == 0;
    if (!bSigned && !_tcsicmp(asArguments[3], _T("unsigned")) == 0) {
      _ftprintf(stderr, _T("Please provide a signedness type (signed, unsigned), not %s.\r\n"), asArguments[3]);
      return 1;
    };
    ISAUINT uValueBitSize = fuParseNumber(asArguments[4]);
    switch (uValueBitSize) {
      case 8: {
        if (bIncrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed char> uValue = SCHAR_MAX;
            uValue++;
          } else {
            msl::utilities::SafeInt<unsigned char> uValue = UCHAR_MAX;
            uValue++;
          };
        } else if (bDecrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed char> uValue = SCHAR_MIN;
            uValue--;
          } else {
            msl::utilities::SafeInt<unsigned char> uValue = 0;
            uValue--;
          };
        } else if (bMultiply) {
          if (bSigned) {
            msl::utilities::SafeInt<signed char> uValue = SCHAR_MIN;
            uValue *= 2;
          } else {
            msl::utilities::SafeInt<unsigned char> uValue = UCHAR_MAX;
            uValue *= 2;
          };
        } else if (bTruncate) {
          // don't care about signedness;
          msl::utilities::SafeInt<unsigned char> uValue = 0;
          unsigned short uLargerValue = USHRT_MAX;
          uValue = uLargerValue;
        } else if (bSignedness) {
          if (bSigned) {
            msl::utilities::SafeInt<signed char> uValue = 0;
            unsigned char uLargerValue = UCHAR_MAX;
            uValue = uLargerValue;
          } else {
            msl::utilities::SafeInt<unsigned char> uValue = 0;
            signed char uSmallerValue = SCHAR_MIN;
            uValue = uSmallerValue;
          };
        };
        break;
      };
      case 16: {
        if (bIncrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed short> uValue = SHRT_MAX;
            uValue++;
          } else {
            msl::utilities::SafeInt<unsigned short> uValue = USHRT_MAX;
            uValue++;
          };
        } else if (bDecrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed short> uValue = SHRT_MIN;
            uValue--;
          } else {
            msl::utilities::SafeInt<unsigned short> uValue = 0;
            uValue--;
          };
        } else if (bMultiply) {
          if (bSigned) {
            msl::utilities::SafeInt<signed short> uValue = SHRT_MIN;
            uValue *= 2;
          } else {
            msl::utilities::SafeInt<unsigned short> uValue = USHRT_MAX;
            uValue *= 2;
          };
        } else if (bTruncate) {
          // don't care about signedness;
          msl::utilities::SafeInt<unsigned short> uValue = 0;
          unsigned int uLargerValue = UINT_MAX;
          uValue = uLargerValue;
        } else if (bSignedness) {
          if (bSigned) {
            msl::utilities::SafeInt<signed short> uValue = 0;
            unsigned short uLargerValue = USHRT_MAX;
            uValue = uLargerValue;
          } else {
            msl::utilities::SafeInt<unsigned short> uValue = 0;
            signed short uSmallerValue = SHRT_MIN;
            uValue = uSmallerValue;
          };
        };
        break;
      };
      case 32: {
        if (bIncrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed int> uValue = INT_MAX;
            uValue++;
          } else {
            msl::utilities::SafeInt<unsigned int> uValue = UINT_MAX;
            uValue++;
          };
        } else if (bDecrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed int> uValue = INT_MIN;
            uValue--;
          } else {
            msl::utilities::SafeInt<unsigned int> uValue = 0;
            uValue--;
          };
        } else if (bMultiply) {
          if (bSigned) {
            msl::utilities::SafeInt<signed int> uValue = INT_MIN;
            uValue *= 2;
          } else {
            msl::utilities::SafeInt<unsigned int> uValue = UINT_MAX;
            uValue *= 2;
          };
        } else if (bTruncate) {
          // don't care about signedness;
          msl::utilities::SafeInt<unsigned int> uValue = 0;
          unsigned __int64 uLargerValue = _UI64_MAX;
          uValue = uLargerValue;
        } else if (bSignedness) {
          if (bSigned) {
            msl::utilities::SafeInt<signed int> uValue = 0;
            unsigned int uLargerValue = UINT_MAX;
            uValue = uLargerValue;
          } else {
            msl::utilities::SafeInt<unsigned int> uValue = 0;
            signed int uSmallerValue = INT_MIN;
            uValue = uSmallerValue;
          };
        };
        break;
      };
      case 64: {
        if (bIncrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed __int64> uValue = _I64_MAX;
            uValue++;
          } else {
            msl::utilities::SafeInt<unsigned __int64> uValue = _UI64_MAX;
            uValue++;
          };
        } else if (bDecrease) {
          if (bSigned) {
            msl::utilities::SafeInt<signed __int64> uValue = _I64_MIN;
            uValue--;
          } else {
            msl::utilities::SafeInt<unsigned __int64> uValue = 0;
            uValue--;
          };
        } else if (bMultiply) {
          if (bSigned) {
            msl::utilities::SafeInt<signed __int64> uValue = _I64_MIN;
            uValue *= 2;
          } else {
            msl::utilities::SafeInt<unsigned __int64> uValue = _UI64_MAX;
            uValue *= 2;
          };
        } else if (bTruncate) {
          _ftprintf(stderr, _T("Sorry, but we cannot truncate a value into a 64-bit type.\r\n"));
          return 1;
        } else if (bSignedness) {
          if (bSigned) {
            msl::utilities::SafeInt<signed __int64> uValue = 0;
            unsigned __int64 uLargerValue = _UI64_MAX;
            uValue = uLargerValue;
          } else {
            msl::utilities::SafeInt<unsigned __int64> uValue = 0;
            signed __int64 uSmallerValue = _I64_MIN;
            uValue = uSmallerValue;
          };
        };
        break;
      };
      default: {
        _ftprintf(stderr, _T("Please provide a bit size (8, 16, 32, or 64), not %s.\r\n"), asArguments[4]);
        return 1;
        break;
      };
    };
  } else {
    _ftprintf(stderr, _T("Invalid test type %s\r\n"), asArguments[1]);
    return 1;
  };
  return 0;
}
