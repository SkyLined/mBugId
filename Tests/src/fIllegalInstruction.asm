IFDEF x86
  .586
  .model flat, stdcall
ENDIF
option casemap :none   

.code

; I want to make sure this function gets a proper stack frame, and the only way I found how to do that is to give
; it an argument.
fIllegalInstruction PROC pDummy:PTR VOID
  NOP ; MASM needs to see a valid instruction first so it knows where to insert the stack frame constructing code.
  db 0FFH, 0FFH, 0CCH
  ; Stop MASM from complaining that the argument is not used; this is a NOP.
  IFDEF x86
    TEST ECX, pDummy
  ELSE
    TEST RCX, pDummy
  ENDIF
  RET
fIllegalInstruction ENDP

END