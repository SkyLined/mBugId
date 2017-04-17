// ----------------------------------------------------------------------------------------------
// Copyright (c) Mattias Högström.
// ----------------------------------------------------------------------------------------------
// This source code is subject to terms and conditions of the Microsoft Public License. A 
// copy of the license can be found in the License.html file at the root of this distribution. 
// If you cannot locate the Microsoft Public License, please send an email to 
// dlr@microsoft.com. By using this source code in any fashion, you are agreeing to be bound 
// by the terms of the Microsoft Public License.
// ----------------------------------------------------------------------------------------------
// You must not remove this notice, or any other, from this software.
// ----------------------------------------------------------------------------------------------

#include <engextcpp.hpp>
#include <dbghelp.h>
#include <stdio.h>
#include <windows.h>
	
class EXT_CLASS : public ExtExtension
{
public:
    EXT_COMMAND_METHOD(Protect);
    EXT_COMMAND_METHOD(MemInfo);
private:

    char PtrToStr_Buffer[128];
	LPTSTR PtrToStr(intptr_t p, LPTSTR buffer);
};



EXT_DECLARE_GLOBALS();

EXT_COMMAND(Protect,
            "Protect page from access\n"
			"  Usage: !Protect <address> <size> <protection>\n"
			"  Example: !Protect 65310000 1000 1\n"
			"  Protection flags:\n"
			"    PAGE_EXECUTE = 0x10\n"
			"    PAGE_EXECUTE_READ = 0x20\n"
			"    PAGE_EXECUTE_READWRITE = 0x40\n"
			"    PAGE_EXECUTE_WRITECOPY = 0x80\n"
			"    PAGE_NOACCESS = 0x01\n"
			"    PAGE_READONLY = 0x02\n"
			"    PAGE_READWRITE = 0x04\n"
			"    PAGE_WRITECOPY = 0x08\n"
			"  \"lm\" can be used to display module boundary addresses\n"
			"  \"!dh <module baseadress>\" can be used to display the PE header\n",
            "{;e;Address; Memory address to protect}{;e;Size; Memory Size to protect}{;e;Mask; Protection mask}{pid;e,d=@$tpid;pid;Process ID}")
{
	  // The way windbg passed arguments
	  // They can be either named or unnamed
	  // pid is a named argument
	  // the rest of them are unnamed
	  
      ULONG64 pid64 = GetArgU64("pid");
      if (GetNumUnnamedArgs() != 3)
      {
         Out("Protect <address> <size> <protection>\n");
         return;
      }
      ULONG64 address64 = GetUnnamedArgU64(0);
      DWORD pId = (DWORD)pid64;
      SIZE_T size = (SIZE_T) GetUnnamedArgU64(1);
      DWORD protect = (DWORD) GetUnnamedArgU64(2);
	  
	  // We are currently executing inside the Windbg process
	  // We need to open the process of the debugging target
	  
      HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS,FALSE,pId);
      if (hProcess != NULL)
      {
		#if defined(_WIN64)
			LPVOID address = Ptr64ToPtr(address64);
		#else
			LPVOID address = (LPVOID)(int)address64;
		#endif


         DWORD old = 0;
         BOOL result = VirtualProtectEx(hProcess, address, size, protect, &old);
         CloseHandle(hProcess);

         if (result)
         {
            Out("New protection (%I32X)\n", protect);
            Out("Old protection (%I32X)\n", old);
         }
         else
         {
            Out("Protect: VirtualProtectEx failed with error code %I32d\n", GetLastError());
         }
      }
      else
      {
         Out("Protect: OpenProcess failed with error code %I32d\n", GetLastError());
      }
}


// Sorry.
//
// It seems I cannot use std:string with WDK
// I would have needed a dynamic string for the formatting
// In order to avoid a new malloc and free for every call
// I chose to use a preallocated buffer PtrToStr_Buffer
// It is not a school book example, but gets the job done.
// 

#define PTRTOSTR(p) PtrToStr((intptr_t)(p), PtrToStr_Buffer)

LPTSTR
EXT_CLASS::PtrToStr(intptr_t p, LPTSTR buffer)
{
	#if defined(_WIN64)
		intptr_t adressHigh = p >> 32;
		intptr_t addressLow = p & 0xffffffff;
		sprintf_s(buffer, sizeof(PtrToStr_Buffer), "%08X`%08X", adressHigh, addressLow);
	#else
		sprintf_s(buffer, sizeof(PtrToStr_Buffer), "%08X", p);
	#endif
	return buffer;
}

EXT_COMMAND(MemInfo,
            "Read memory information\n"
			"  Usage: !MemInfo <address>\n",
            "{;e;Address; Memory address to protect}{pid;e,d=@$tpid;pid;Process ID}")
{
    ULONG64 pid64 = GetArgU64("pid");
	DWORD pId = (DWORD)pid64;
    if (GetNumUnnamedArgs() != 1)
    {
        Out("Protect <address> <size> <protection>\n");
        return;
    }
    ULONG64 address64 = GetUnnamedArgU64(0);

	HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS,FALSE,pId);
    if (hProcess != NULL)
    {
		#if defined(_WIN64)
        LPVOID address = Ptr64ToPtr(address64);
		#else
		LPVOID address = (LPVOID)(int)address64;
		#endif

		MEMORY_BASIC_INFORMATION buffer;
		SIZE_T bufferLen = sizeof(buffer);
		SIZE_T nBytes = VirtualQueryEx(hProcess, address, &buffer, bufferLen);
		if (nBytes != 0)
		{
			Out("MEMORY_BASIC_INFORMATION\n");
			
			Out("  BaseAddress = %s\n", PTRTOSTR(buffer.BaseAddress));
			Out("  AllocationBase = %s\n", PTRTOSTR(buffer.AllocationBase));
			if (IsCurMachine32())
			{
				Out("  RegionSize = %I32X\n", buffer.RegionSize);
			}
			else
			{
				Out("  RegionSize = %I64X\n", buffer.RegionSize);
			}
			Out("  AllocationProtect = %I32X\n", buffer.AllocationProtect);
			Out("  State = %I32X\n", buffer.State);
			Out("  Protect = %I32X\n", buffer.Protect);
			Out("  Type = %I32X\n", buffer.Type);
		}
		else
		{
			Out("Failed to read memory information\n");
		}
		CloseHandle(hProcess);
	}
	else
	{
		Out("Cannot Open Process %d\n", pId);
	}
}