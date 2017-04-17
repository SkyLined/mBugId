IFDEF x86
  .586
  .model flat, stdcall
ENDIF
option casemap :none   

.code

fJump PROC, pAddress:PTR VOID
  IFDEF x86
    JMP pAddress
  ELSE
    JMP RCX ; stdcall on x86, __fastcall on x64
  ENDIF
  RET
fJump ENDP

END