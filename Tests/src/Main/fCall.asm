IFDEF x86
  .586
  OPTION CASEMAP :NONE
  .MODEL flat, stdcall
ENDIF
_TEXT SEGMENT
  PUBLIC fCall
    IFDEF x86
      fCall PROC pAddress:PTR
      ; Stack frame code gets added automatically
      ; function code
      CALL  pAddress
      ; Stack frame code gets added automatically
    ELSE
      fCall PROC FRAME
      ; Create stack frame
      PUSH  RBP
      .PUSHREG RBP
      MOV   RBP, RSP
      .SETFRAME RBP, 0
      .ENDPROLOG
      ; function code
      CALL RCX
      ; Unwind stack frame
      LEAVE
    ENDIF
    RET
  fCall ENDP
_TEXT ENDS
END
