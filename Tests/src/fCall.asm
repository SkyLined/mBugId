IFDEF x86
  .586
  .model flat, stdcall
ENDIF
option casemap :none   

.code

fCall PROC pAddress:PTR VOID
  IFDEF x86
    CALL pAddress
  ELSE
    CALL RCX ; stdcall on x86, __fastcall on x64
  ENDIF
  RET
fCall ENDP

END