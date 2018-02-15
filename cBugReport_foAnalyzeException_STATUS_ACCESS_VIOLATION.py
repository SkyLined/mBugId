import re, struct;
from .mAccessViolation import fUpdateReportForTypeIdAndAddress as fUpdateAccessViolationReportForTypeIdAndAddress;
from mWindowsAPI import cVirtualAllocation;

def cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION(oBugReport, oProcess, oException):
  oCdbWrapper = oProcess.oCdbWrapper;
  # Parameter[0] = access type (0 = read, 1 = write, 8 = execute)
  # Parameter[1] = address
  assert len(oException.auParameters) == 2, \
      "Unexpected number of access violation exception parameters (%d vs 2)" % len(oException.auParameters);
  # Access violation: add the type of operation and the location to the exception id.
  sViolationTypeId = {0:"R", 1:"W", 8:"E"}.get(oException.auParameters[0], "?");
  uAccessViolationAddress = oException.auParameters[1];
  if uAccessViolationAddress == 0xFFFFFFFFFFFFFFFF and sViolationTypeId == "R":
    # In x64 mode, current processors will thrown an exception when you use an address larger than 0x7FFFFFFFFFFF and
    # smaller than 0xFFFF800000000000. In such cases cdb reports incorrect information in the exception parameters,
    # e.g. the address is always reported as 0xFFFFFFFFFFFFFFFF and the access type is always "read".
    # A partial work-around is to get the address from the last instruction output, which can be retrieved by asking
    # cdb to output disassembly and address after each command. This may also tell us if the access type was "execute".
    oProcess.fasExecuteCdbCommand(
      sCommand = ".prompt_allow +dis +ea;",
      sComment = "Enable disassembly and address in cdb prompt",
    );
    # Do this twice in case the first time requires loading symbols, which can output junk that makes parsing ouput difficult.
    oProcess.fasExecuteCdbCommand( \
      sCommand = "~s;",
      sComment = "Show disassembly and optional symbol loading stuff",
    );
    asLastInstructionAndAddress = oProcess.fasExecuteCdbCommand(
      sCommand = "~s;",
      sComment = "Show disassembly",
      bOutputIsInformative = True,
    );
    # Revert to not showing disassembly and address:
    oProcess.fasExecuteCdbCommand( \
      sCommand = ".prompt_allow -dis -ea;",
      sComment = "Revert to clean cdb prompt",
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
    assert len(asLastInstructionAndAddress) == 1, \
        "Unexpected last instruction output:\r\n%r" % "\r\n".join(asLastInstructionAndAddress);
    oEIPOutsideAllocatedMemoryMatch = re.match("^%s$" % "".join([
      r"([0-9`a-f]+)", r"\s+", r"\?\?", r"\s+", r"\?\?\?" # address   spaces "??" spaces "???"
    ]), asLastInstructionAndAddress[0]);
    if oEIPOutsideAllocatedMemoryMatch:
      sAddress = oEIPOutsideAllocatedMemoryMatch.group(1);
      sViolationTypeId = "E";
    else:
      oLastInstructionMatch = re.match("^%s$" % "".join([
        r"[0-9`a-f]+", r"\s+",      # address   spaces
        r"[0-9`a-f]+", r"\s+",      # opcode   spaces
        r"\w+", r"\s+",             # instruction   spaces
        r"(?:",                     # either{
          r"([^\[,]+,.+)",          #   (destination operand that does not reference memory "," source operand )
        r"|",                       # }or{
          ".*"                      #   any other combination of operands
        r")",                       # }
        r"(?:",                     # either{
          r"\ws:",                  #   segment register ":"
          r"(?:[0-9a-f`]{4}:)?",    #   optional { segment value ":" }
          r"([0-9a-f`]+)",          #   (sAddress1)
          r"=" r"(?:",              # "=" either {
            r"\?+",                 #    "???????" <cannot be read>
          "|",                      # } or {
            r"([0-9`a-f]+)",        #   (sValue)  <memory at address can be read>
          "|",                      # } or {
            r"\{",                  #   "{"
              r".+",                #      symbol
              r"\s+",               #      spaces
              r"\(([0-9`a-f]+)\)",  #     "(" (sAddress2) ")"
            r"\}",                  #   "}"
          ")",
        r"|",                       # }or{
          r"\{([0-9`a-f]+)\}",      #   "{" (sAddress3) "}"
        r")",                       # }
      ]), asLastInstructionAndAddress[0]);
      assert oLastInstructionMatch, \
          "Unexpected last instruction output:\r\n%s" % "\r\n".join(asLastInstructionAndAddress);
      sDestinationOperandThatDoesNotReferenceMemory, sAddress1, sValue, sAddress2, sAddress3 = oLastInstructionMatch.groups();
      sAddress = sAddress1 or sAddress2 or sAddress3;
      if sAddress1:
        if sDestinationOperandThatDoesNotReferenceMemory:
          # The destination operand does not reference memory, so this must be a read AV
          sViolationTypeId = "R";
        elif sAddress1 and sValue:
          # The adress referenced can be read, so it must be write AV
          sViolationTypeId = "W";
        else:
          sViolationTypeId = "?";
          sViolationTypeNotes = " (the type of accesss must be read or write, but cannot be determined)";
      else:
        sViolationTypeId = "E";
    uAccessViolationAddress = long(sAddress.replace("`", ""), 16);
  oBugReport.atxMemoryRemarks.append(("Access violation", uAccessViolationAddress, None)); # TODO Find out size of access

  
  
  if sViolationTypeId == "E":
    # Hide the top stack frame if it is for the address at which the execute access violation happened:
    if oBugReport and oBugReport.oStack and oBugReport.oStack.aoFrames \
        and oBugReport.oStack.aoFrames[0].uInstructionPointer == uAccessViolationAddress:
      oBugReport.oStack.aoFrames[0].sIsHiddenBecause = "called address";
  
  fUpdateAccessViolationReportForTypeIdAndAddress(
      oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress);

  if sViolationTypeId == "?":
    oBugReport.sBugDescription += " (the type-of-accesss code was 0x%X)" % oException.auParameters[0];
  return oBugReport;

