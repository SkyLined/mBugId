Project is compiled with the Windows Driver Kit (WDK).
http://www.microsoft.com/whdc/devtools/WDK/default.mspx

Remember to set up the include and library paths to the debug sdk.

set DBGSDK_INC_PATH=C:\source\sdk\inc
set DBGSDK_LIB_PATH=C:\source\sdk\lib
set DBGLIB_LIB_PATH=C:\source\sdk\lib


If you have the Debugging tools for Windows installed.
You can find the sdk in the following location(s).

C:\Program Files (x86)\Debugging Tools for Windows (x86)\sdk
C:\Program Files\Debugging Tools for Windows (x64)\sdk

I have copied them into this package because the build command
had problems with long paths containing spaces.

The source supports both x86 and x64 through the _WIN64 define
The generated library depends on the WDK Build Environment you choose to build with.
