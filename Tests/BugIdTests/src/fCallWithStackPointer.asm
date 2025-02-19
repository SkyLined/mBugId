;## Function prefix #####################################
IFNDEF _WIN64

.586
.MODEL flat, stdcall
.CODE
ALIGN 8
fCallWithStackPointer  PROC pAddress:PTR
  ; Code to create new stack frame is added automatically

ELSE

.CODE
ALIGN 16
fCallWithStackPointer  PROC FRAME
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
  ; jump ahead using a CALL instruction
  CALL    pCallTarget

pCallTarget LABEL NEAR
  ; restore the old stack pointer
  MOV     ESP, EAX
ELSE
  ; save the old stack pointer in a volatile register
  MOV     RAX, RSP
  ; set the stack pointer to the address in the function argument
  MOV     RSP, RCX
  ; jump ahead using a CALL instruction
  CALL    pCallTarget

pCallTarget LABEL NEAR
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
fCallWithStackPointer ENDP
END