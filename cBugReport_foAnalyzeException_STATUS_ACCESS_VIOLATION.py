import re;

from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from .mAccessViolation import fUpdateReportForProcessThreadTypeIdAndAddress as fUpdateReportForProcessThreadAccessViolationTypeIdAndAddress;

grbEIPOutsideAllocatedMemory = re.compile(
  rb"^"
  rb"([0-9`a-f]+)"            # (address)
  rb"\s+"                     # whitespace
  rb"\?\?"                    # "??"
  rb"\s+"                     # whitespace
  rb"\?\?\?"                  # "???"
);

grbInstruction = re.compile(
  rb"^"
  rb"[0-9`a-f]+"              # address
  rb"\s+"                     # whitespace
  rb"[0-9`a-f]+"              # opcode
  rb"\s+"                     # whitespace
  rb"\w+"                     # instruction
  rb"\s+"                     # whitespace
  rb"(?:"                     # either{
    rb"([^\[,]+,.+)"          #   (destination operand that does not reference memory "," source operand )
  rb"|"                       # }or{
    rb".*"                    #   any other combination of operands
  rb")"                       # }
  rb"(?:"                     # either{
    rb"\ws:"                  #   segment register ":"
    rb"(?:[0-9a-f`]{4}:)?"    #   optional { segment value ":" }
    rb"([0-9a-f`]+)"          #   (sAddress1)
    rb"="                     #   "="
    rb"(?:"                   #   either {
      rb"\?+"                 #     "???????" <cannot be read>
    rb"|"                     #   } or {
      rb"([0-9`a-f]+)"        #     (sValue)  <memory at address can be read>
    rb"|"                     #   } or {
      rb"\{"                  #     "{"
      rb".+"                  #     symbol
      rb"\s+"                 #     spaces
      rb"\(([0-9`a-f]+)\)"    #     "(" (sAddress2) ")"
      rb"\}"                  #     "}"
    rb")"                     #   }
  rb"|"                       # } or {
    rb"\{([0-9`a-f]+)\}"      #   "{" (sAddress3) "}"
  rb")"                       # }
  rb"$"
);
def cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION(oBugReport, oProcess, oThread, oException):
  oCdbWrapper = oProcess.oCdbWrapper;
  # Parameter[0] = access type (0 = read, 1 = write, 8 = execute)
  # Parameter[1] = address
  assert len(oException.auParameters) == 2, \
      "Unexpected number of access violation exception parameters (%d vs 2)" % len(oException.auParameters);
  # Access violation: add the type of operation and the location to the exception id.
  sViolationTypeId = {0:"R", 1:"W", 8:"E"}.get(oException.auParameters[0], "?");
  sViolationTypeNotes = None;
  uAccessViolationAddress = oException.auParameters[1];
  if uAccessViolationAddress == 0xFFFFFFFFFFFFFFFF and sViolationTypeId == "R":
    # In x64 mode, current processors will thrown an exception when you use an address larger than 0x7FFFFFFFFFFF and
    # smaller than 0xFFFF800000000000. In such cases cdb reports incorrect information in the exception parameters,
    # e.g. the address is always reported as 0xFFFFFFFFFFFFFFFF and the access type is always "read".
    # A partial work-around is to get the address from the last instruction output, which can be retrieved by asking
    # cdb to output disassembly and address after each command. This may also tell us if the access type was "execute".
    oProcess.fasbExecuteCdbCommand(
      sbCommand = b".prompt_allow +dis +ea;",
      sb0Comment = b"Enable disassembly and address in cdb prompt",
    );
    # Do this twice in case the first time requires loading symbols, which can output junk that makes parsing ouput difficult.
    oProcess.fasbExecuteCdbCommand( \
      sbCommand = b"~s;",
      sb0Comment = b"Show disassembly and optional symbol loading stuff",
    );
    asbLastInstructionAndAddress = oProcess.fasbExecuteCdbCommand(
      sbCommand = b"~s;",
      sb0Comment = b"Show disassembly",
      bOutputIsInformative = True,
    );
    # Revert to not showing disassembly and address:
    oProcess.fasbExecuteCdbCommand( \
      sbCommand = b".prompt_allow -dis -ea;",
      sb0Comment = b"Revert to clean cdb prompt",
    );
    # Sample output:
    # |00007ffd`420b213e 488b14c2        mov     rdx,qword ptr [rdx+rax*8] ds:00007df5`ffb60000=????????????????
    # or
    # |60053594 ff7008          push    dword ptr [eax+8]    ds:002b:00000008=????????
    # or
    # |00007ff6`e7ab1204 ffe1            jmp     rcx {c0c0c0c0`c0c0c0c0}
    # or
    # |00000000`7fffffff ??              ???
    # or
    # |00007ff9`b6f1a904 488b8d500d0000  mov     rcx,qword ptr [rbp+0D50h] ss:00000244`4124f590=0000024441210240
    assert len(asbLastInstructionAndAddress) == 1, \
        "Unexpected last instruction output:\r\n%r" % "\r\n".join(asbLastInstructionAndAddress);
    obEIPOutsideAllocatedMemoryMatch = grbEIPOutsideAllocatedMemory.match(asbLastInstructionAndAddress[0]);
    if obEIPOutsideAllocatedMemoryMatch:
      sbAddress = obEIPOutsideAllocatedMemoryMatch.group(1);
      sViolationTypeId = "E";
    else:
      obLastInstructionMatch = grbInstruction.match(asbLastInstructionAndAddress[0]);
      assert obLastInstructionMatch, \
          "Unexpected last instruction output:\r\n%s" % "\r\n".join(asbLastInstructionAndAddress);
      (sbDestinationOperandThatDoesNotReferenceMemory, sbAddress1, sbValue, sbAddress2, sbAddress3) = \
          obLastInstructionMatch.groups();
      sbAddress = sbAddress1 or sbAddress2 or sbAddress3;
      if sbAddress1:
        if sbDestinationOperandThatDoesNotReferenceMemory:
          # The destination operand does not reference memory, so this must be a read AV
          sViolationTypeId = "R";
        elif sbAddress1 and sbValue:
          # The adress referenced can be read, so it must be write AV
          sViolationTypeId = "W";
        else:
          sViolationTypeId = "?";
          sViolationTypeNotes = " (the type of accesss must be read or write, but cannot be determined)";
      else:
        sViolationTypeId = "E";
    uAccessViolationAddress = fu0ValueFromCdbHexOutput(sbAddress);
  oBugReport.atxMemoryRemarks.append(("Access violation", uAccessViolationAddress, None)); # TODO Find out size of access
  
  if sViolationTypeId == "E":
    # Hide the top stack frame if it is for the address at which the execute access violation happened:
    if oBugReport and oBugReport.o0Stack and oBugReport.o0Stack.aoFrames \
        and oBugReport.o0Stack.aoFrames[0].u0InstructionPointer is uAccessViolationAddress:
      oBugReport.o0Stack.aoFrames[0].s0IsHiddenBecause = "called address";
  
  fUpdateReportForProcessThreadAccessViolationTypeIdAndAddress(
    oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress
  );

  if sViolationTypeNotes:
    oBugReport.s0BugDescription += sViolationTypeNotes; # Shouldn't be None
  return oBugReport;

