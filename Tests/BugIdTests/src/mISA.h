#define WIN32_LEAN_AND_MEAN

#include <tchar.h>
#include <windows.h>

// Use Instruction Set Architecture (ISA) specific (unsigned) integers:
#ifdef _WIN64
  #define ISAINT signed __int64
  #define ISAUINT unsigned __int64
#else
  #define ISAINT INT
  #define ISAUINT UINT
#endif
