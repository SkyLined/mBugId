extern "C" {
  // even the ones that don't need arguments have one
  // because name mangling sucks and this makes the
  // prefix and postfix code in all of them similar.
  VOID __stdcall fCall(PVOID);
  VOID __stdcall fJump(PVOID);
  VOID __stdcall fRet(PVOID);
  VOID __stdcall fIllegalInstruction(PVOID);
  VOID __stdcall fIntegerOverflow(PVOID);
  VOID __stdcall fPrivilegedInstruction(PVOID);
  VOID __stdcall fCallWithStackPointer(PVOID);
  VOID __stdcall fRetWithStackPointer(PVOID);
  VOID __stdcall fPushWithStackPointer(PVOID);
  VOID __stdcall fPopWithStackPointer(PVOID);
};
