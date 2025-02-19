;## Function prefix #####################################
IFNDEF _WIN64

.586
.MODEL flat, stdcall
.CODE
ALIGN 8
fPushWithStackPointer PROC pAddress:PTR
  ; Code to create new stack frame is added automatically

ELSE

.CODE
ALIGN 16
fPushWithStackPointer PROC FRAME
  ; Create new stack frame
  PUSH    RBP
  .PUSHREG RBP
  MOV     RBP, RSP
  .SETFRAME RBP, 0
  .ENDPROLOG

ENDIF

;## Function code #########################################
IFNDEF _WIN64
  ; save the old stack pointer in a volatile register
  MOV     EAX, ESP
  ; set the stack pointer to the address in the function argument
  MOV     ESP, pAddress
  ; push a value onto the stack
  PUSH    EAX
  ; restore the old stack pointer
  MOV     ESP, EAX
ELSE
  ; save the old stack pointer in a volatile register
  MOV     RAX, RSP
  ; set the stack pointer to the address in the function argument
  MOV     RSP, RCX
  ; push a value onto the stack
  PUSH    RAX
  ; restore the old stack pointer
  MOV     RSP, RAX
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
fPushWithStackPointer ENDP
END