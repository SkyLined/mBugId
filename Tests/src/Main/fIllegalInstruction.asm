IFDEF x86
  .586
  OPTION CASEMAP :NONE
  .MODEL flat, stdcall
ENDIF
_TEXT SEGMENT
  PUBLIC fIllegalInstruction
    IFDEF x86
      fIllegalInstruction PROC
      ; Create stack frame (because there are no arguments)
      PUSH  EBP
      MOV   EBP, ESP
    ELSE
      fIllegalInstruction PROC FRAME
      ; Create stack frame
      PUSH  RBP
      .PUSHREG RBP
      MOV   RBP, RSP
      .SETFRAME RBP, 0
      .ENDPROLOG
    ENDIF
    ; function code
    db 0FFH, 0FFH, 0CCH
    ; Unwind stack frame
    LEAVE
    RET
  fIllegalInstruction ENDP
_TEXT ENDS
END
