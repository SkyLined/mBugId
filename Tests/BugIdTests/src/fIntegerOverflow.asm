;## Function prefix #####################################
IFNDEF _WIN64

.586
.MODEL flat, stdcall
.CODE
ALIGN 8
fIntegerOverflow PROC pUnused:PTR
  ; Code to create new stack frame is added automatically

ELSE

.CODE
ALIGN 16
fIntegerOverflow PROC FRAME
  ; Create new stack frame
  PUSH    RBP
  .PUSHREG RBP
  MOV     RBP, RSP
  .SETFRAME RBP, 0
  .ENDPROLOG

ENDIF

;## Function code #########################################
  ; trigger integer overflow
  MOV   EAX, 80000000H
  CDQ
  IDIV  EDX

;## Function postfix ########################################
IFNDEF _WIN64
  MOV EAX, pUnused ; To avoid 
  ; Code to restore old stack frame is added automatically
  RET 4
ELSE    
  ; Restore old stack frame
  LEAVE
  RET
ENDIF
fIntegerOverflow ENDP
END