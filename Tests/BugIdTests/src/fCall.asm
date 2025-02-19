;## Function prefix #####################################
IFNDEF _WIN64

.586
.MODEL flat, stdcall
.CODE
ALIGN 8
fCall PROC pAddress:PTR
  ; Code to create new stack frame is added automatically

ELSE

.CODE
ALIGN 16
fCall PROC FRAME
  ; Create new stack frame
  PUSH    RBP
  .PUSHREG RBP
  MOV     RBP, RSP
  .SETFRAME RBP, 0
  .ENDPROLOG

ENDIF

;## Function code #########################################
IFNDEF _WIN64
  CALL    pAddress
ELSE  
  CALL    RCX
ENDIF

;## Function postfix ########################################
IFNDEF _WIN64
  ; Code to restore old stack frame is added automatically
  RET 4
ELSE    
  ; Restore old stack frame
  LEAVE
  RET
ENDIF
fCall ENDP
END