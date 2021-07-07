IFDEF x86
  .586
  OPTION CASEMAP :NONE
  .MODEL flat, stdcall
ENDIF
_TEXT SEGMENT
  PUBLIC fJump
    IFDEF x86
      fJump PROC pAddress:PTR
      ; Stack frame code gets added automatically
      ; function code
      JMP  pAddress
      ; Stack frame code gets added automatically
    ELSE
      fJump PROC FRAME
      ; Create stack frame
      PUSH  RBP
      .PUSHREG RBP
      MOV   RBP, RSP
      .SETFRAME RBP, 0
      .ENDPROLOG
      ; function code
      JMP RCX
      ; Unwind stack frame
      LEAVE
    ENDIF
    RET
  fJump ENDP
_TEXT ENDS
END
