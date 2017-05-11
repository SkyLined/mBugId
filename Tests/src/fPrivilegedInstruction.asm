IFDEF x86
  .586
  .model flat, stdcall
ENDIF
option casemap :none   

.code

; I want to make sure this function gets a proper stack frame, and the only way I found how to do that is to give
; it an argument.
fPrivilegedInstruction PROC pDummy:PTR VOID
  CLI
  ; Stop MASM from complaining that the argument is not used; this is a NOP.
  IFDEF x86
    TEST ECX, pDummy
  ELSE
    TEST RCX, pDummy
  ENDIF
  RET
fPrivilegedInstruction ENDP

END