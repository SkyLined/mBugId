;## Function prefix #####################################
IFNDEF _WIN64

.586
.MODEL flat, stdcall
.CODE
ALIGN 8
fPopWithStackPointer PROC pAddress:PTR
  ; Code to create new stack frame is added automatically

ELSE

.CODE
ALIGN 16
fPopWithStackPointer PROC FRAME
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
  ; pop a value from the stack into a volatile register
  POP     EDX
  ; restore the old stack pointer
  MOV     ESP, EAX
ELSE
  ; save the old stack pointer in a volatile register
  MOV     RAX, RSP
  ; set the stack pointer to the address in the function argument
  MOV     RSP, RCX
  ; pop a value from the stack into a volatile register
  POP     RDX
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
fPopWithStackPointer ENDP
END