IFDEF x86
  .586
  OPTION CASEMAP :NONE
  .MODEL flat, stdcall
ENDIF
_TEXT SEGMENT
  PUBLIC fIntegerOverflow
    IFDEF x86
      fIntegerOverflow PROC
      ; Create stack frame (because there are no arguments)
      PUSH  EBP
      MOV   EBP, ESP
    ELSE
      fIntegerOverflow PROC FRAME
      ; Create stack frame
      PUSH  RBP
      .PUSHREG RBP
      MOV   RBP, RSP
      .SETFRAME RBP, 0
      .ENDPROLOG
    ENDIF
    ; function code
    MOV   EAX, 80000000H
    CDQ
    IDIV  EDX
    ; Unwind stack frame
    LEAVE
    RET
  fIntegerOverflow ENDP
_TEXT ENDS
END
