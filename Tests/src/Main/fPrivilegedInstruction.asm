IFDEF x86
  .586
  OPTION CASEMAP :NONE
  .MODEL flat, stdcall
ENDIF
_TEXT SEGMENT
  PUBLIC fPrivilegedInstruction
    IFDEF x86
      fPrivilegedInstruction PROC
      ; Create stack frame (because there are no arguments)
      PUSH  EBP
      MOV   EBP, ESP
    ELSE
      ; Create stack frame
      fPrivilegedInstruction PROC FRAME
      PUSH  RBP
      .PUSHREG RBP
      MOV   RBP, RSP
      .SETFRAME RBP, 0
      .ENDPROLOG
    ENDIF
    ; function code
    CLI
    ; Unwind stack frame
    LEAVE
    RET
  fPrivilegedInstruction ENDP
_TEXT ENDS
END
