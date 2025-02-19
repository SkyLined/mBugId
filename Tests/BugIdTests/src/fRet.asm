;## Function prefix #####################################
IFNDEF _WIN64

.586
.MODEL flat, stdcall
.CODE
ALIGN 8
fRet PROC pAddress:PTR
  ; Code to create new stack frame is added automatically

ELSE

.CODE
ALIGN 16
fRet PROC FRAME
  ; Create new stack frame
  PUSH    RBP
  .PUSHREG RBP
  MOV     RBP, RSP
  .SETFRAME RBP, 0
  .ENDPROLOG

ENDIF

;## Function code #########################################
IFNDEF _WIN64
  ; EBP now points one DWORD below the return address
  MOV     EAX, pAddress
  MOV     [EBP + 4], EAX
ELSE
  ; EBP now points one QWORD below the return address
  ; The argument passed to this function is in RCX
  MOV     [RBP + 8], RCX
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
fRet ENDP
END