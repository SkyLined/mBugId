import re;
from cVirtualAllocation import cVirtualAllocation;
from cHeapAllocation import cHeapAllocation;
from cThreadEnvironmentBlock import cThreadEnvironmentBlock;
from dxConfig import dxConfig;
from fsGetNumberDescription import fsGetNumberDescription;
from ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from fSetBugReportPropertiesForAccessViolationUsingHeapAllocation import fSetBugReportPropertiesForAccessViolationUsingHeapAllocation;
from sBlockHTMLTemplate import sBlockHTMLTemplate;

ddtsDetails_uSpecialAddress_sISA = {
  # There are a number of values that are very close to eachother, and because an offset is likely to be added when
  # reading using a pointer, having all of them here does not offer extra information. So, I've limited it to values
  # that are sufficiently far away from eachother to be recognisable after adding offsets.
  "x86": {              # Id                      Description                                           Security impact
            # https://en.wikipedia.org/wiki/Magic_number_(programming)#Magic_debug_values
            0x00000000: ("NULL",                  "a NULL ptr",                                         None),
            
            0xA0A0A0A0: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary", "Potentially exploitable security issue"),       
            # https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
            0xABCDAAAA: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a heap block header", "Potentially exploitable security issue"),
            0xABCDBBBB: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a full heap block header", "Potentially exploitable security issue"),       
            
            0xBBADBEEF: ("Assertion",             "an address that indicates an assertion has failed",  None),
            
            0xBAADF00D: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            
            0xCCCCCCCC: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            
            0xC0C0C0C0: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            
            0xCDCDCDCD: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            
            0xD0D0D0D0: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            # https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
            0xDCBAAAAA: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a heap block header", "Potentially exploitable security issue"),
            0xDCBABBBB: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a full heap block header", "Potentially exploitable security issue"),
            
            0xDDDDDDDD: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
            
            0xE0E0E0E0: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),             
            # https://hg.mozilla.org/releases/mozilla-beta/rev/8008235a2429
            0xE4E4E4E4: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            0xE5E5E5E5: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
            
            0xF0090100: ("Poison",                "a pointer read from poisoned memory",                "Potentially exploitable security issue"),
            
            0xF0DE7FFF: ("Poison",                "a pointer read from poisoned memory",                "Potentially exploitable security issue"),
            
            0xF0F0F0F0: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
            
            0xFDFDFDFD: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary", "Potentially exploitable security issue"),
            
            0xFEEEFEEE: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
  },
  "x64": {              # Id                      Description                                           Security impact
    0x0000000000000000: ("NULL",                  "a NULL ptr",                                         None),
    # Note that on x64, addresses with the most significant bit set cannot be allocated in user-land. Since BugId is expected to analyze only user-land
    # applications, accessing such an address is not expected to be an exploitable security issue.
    0xBAADF00DBAADF00D: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xCCCCCCCCCCCCCCCC: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xC0C0C0C0C0C0C0C0: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xCDCDCDCDCDCDCDCD: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xD0D0D0D0D0D0D0D0: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xDDDDDDDDDDDDDDDD: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
    0xF0F0F0F0F0F0F0F0: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
    0xF0DE7FFFF0DE7FFF: ("Poison",                "a pointer read from poisoned memory",                None),
    0xF0090100F0090100: ("Poison",                "a pointer read from poisoned memory",                None),
    0xFEEEFEEEFEEEFEEE: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
    # https://hg.mozilla.org/releases/mozilla-beta/rev/8008235a2429
    0xE4E4E4E4E4E4E4E4: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xE5E5E5E5E5E5E5E5: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
  },
};

def cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION(oBugReport, oProcess, oException):
  # Parameter[0] = access type (0 = read, 1 = write, 8 = execute)
  # Parameter[1] = address
  assert len(oException.auParameters) == 2, \
      "Unexpected number of access violation exception parameters (%d vs 2)" % len(oException.auParameters);
  # Access violation: add the type of operation and the location to the exception id.
  sViolationTypeId = {0:"R", 1:"W", 8:"E"}.get(oException.auParameters[0], "_");
  sViolationTypeDescription = {0:"reading", 1:"writing", 8:"executing"}.get(oException.auParameters[0], "accessing");
  sViolationTypeNotes = sViolationTypeId == "_" and " (the type-of-accesss code was 0x%X)" % oException.auParameters[0] or "";
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
      sViolationTypeDescription = "executing";
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
          sViolationTypeDescription = "reading";
        elif sAddress1 and sValue:
          # The adress referenced can be read, so it must be write AV
          sViolationTypeId = "W";
          sViolationTypeDescription = "writing";
        else:
          sViolationTypeId = "_";
          sViolationTypeDescription = "accessing";
          sViolationTypeNotes = " (the type of accesss must be read or write, but cannot be determined)";
      else:
        sViolationTypeId = "E";
        sViolationTypeDescription = "executing";
    uAccessViolationAddress = long(sAddress.replace("`", ""), 16);
  oBugReport.atxMemoryRemarks.append(("Access violation", uAccessViolationAddress, None)); # TODO Find out size of access
  
  if sViolationTypeId == "E":
    # Hide the top stack frame if it is for the address at which the execute access violation happened:
    if oBugReport and oBugReport.oStack and oBugReport.oStack.aoFrames \
        and oBugReport.oStack.aoFrames[0].uInstructionPointer == uAccessViolationAddress:
      oBugReport.oStack.aoFrames[0].sIsHiddenBecause = "called address";
  
  dtsDetails_uSpecialAddress = ddtsDetails_uSpecialAddress_sISA[oProcess.sISA];
  for (uSpecialAddress, (sSpecialAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
    sBugDescription = "Access violation while %s memory at 0x%X using %s." % \
        (sViolationTypeDescription, uAccessViolationAddress, sAddressDescription);
    iOffset = uAccessViolationAddress - uSpecialAddress;
    if iOffset != 0:
      uOverflow = {"x86": 1 << 32, "x64": 1 << 64}[oProcess.sISA];
      if iOffset > dxConfig["uMaxAddressOffset"]: # Maybe this is wrapping:
        iOffset -= uOverflow;
      elif iOffset < -dxConfig["uMaxAddressOffset"]: # Maybe this is wrapping:
        iOffset += uOverflow;
    uOffset = abs(iOffset);
    if uOffset <= dxConfig["uMaxAddressOffset"]:
      sSign = iOffset < 0 and "-" or "+";
      sOffset = iOffset != 0 and "%s%s" % (sSign, fsGetNumberDescription(uOffset, sSign)) or "";
      oBugReport.sBugTypeId = "AV%s@%s%s" % (sViolationTypeId, sSpecialAddressId, sOffset);
      oBugReport.sBugDescription = sBugDescription;
      oBugReport.sSecurityImpact = sSecurityImpact;
      break;
  else:
    # This is not a special marker or NULL, so it must be an invalid pointer
    # Get information about the memory region:
    oHeapAllocation = oProcess.foGetHeapAllocationForAddress(uAccessViolationAddress);
    if oHeapAllocation:
      oBugReport.atxMemoryRemarks.extend(oHeapAllocation.fatxMemoryRemarks());
      fSetBugReportPropertiesForAccessViolationUsingHeapAllocation(
        oBugReport, \
        uAccessViolationAddress, sViolationTypeId, sViolationTypeDescription, \
        oHeapAllocation, \
        oProcess.uPointerSize, oProcess.oCdbWrapper.bGenerateReportHTML,
      );
      if oProcess.oCdbWrapper.bGenerateReportHTML:
        sCdbHeapOutputHTML = sBlockHTMLTemplate % {
          "sName": "Heap information for block near address 0x%X" % (uAccessViolationAddress,),
          "sCollapsed": "Collapsed",
          "sContent": "<pre>%s</pre>" % "\r\n".join([
            oProcess.oCdbWrapper.fsHTMLEncode(sCdbHeapOutputLine, uTabStop = 8)
            for sCdbHeapOutputLine in oHeapAllocation.asCdbHeapOutput
          ])
        };
        oBugReport.asExceptionSpecificBlocksHTML.append(sCdbHeapOutputHTML);
    else:
      oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uAccessViolationAddress);
      # See is page heap has more details on the address at which the access violation happened:
      if not oVirtualAllocation:
        oBugReport.sBugTypeId = "AV%s@Invalid" % sViolationTypeId;
        oBugReport.sBugDescription = "Access violation while %s memory at invalid address 0x%X." % (sViolationTypeDescription, uAccessViolationAddress);
        oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled.";
      else:
        oThreadEnvironmentBlock = cThreadEnvironmentBlock.foCreateForCurrentThread(oProcess);
        uOffsetFromTopOfStack = uAccessViolationAddress - oThreadEnvironmentBlock.uStackTopAddress;
        uOffsetFromBottomOfStack = oThreadEnvironmentBlock.uStackBottomAddress - uAccessViolationAddress;
        if uOffsetFromTopOfStack >= 0 and uOffsetFromTopOfStack <= oProcess.uPageSize:
          oBugReport.sBugTypeId = "AV%s[Stack]+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromTopOfStack));
          oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes passed the top of the stack at 0x%X." % \
              (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromTopOfStack, uOffsetFromTopOfStack, oThreadEnvironmentBlock.uStackTopAddress);
          oBugReport.sSecurityImpact = "Potentially exploitable security issue.";
        elif uOffsetFromBottomOfStack >= 0 and uOffsetFromBottomOfStack <= oProcess.uPageSize:
          oBugReport.sBugTypeId = "AV%s[Stack]-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromBottomOfStack));
          oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes before the bottom of the stack at 0x%X." % \
              (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromBottomOfStack, uOffsetFromBottomOfStack, oThreadEnvironmentBlock.uStackTopAddress);
          oBugReport.sSecurityImpact = "Potentially exploitable security issue.";
        else:
          if not oVirtualAllocation:
            oBugReport.sBugTypeId = "AV%s@Unallocated" % sViolationTypeId;
            oBugReport.sBugDescription = "Access violation while %s unallocated memory at 0x%X." % (sViolationTypeDescription, uAccessViolationAddress);
            oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or memory be allocated at the address.";
          else:
            if oProcess.oCdbWrapper.bGenerateReportHTML:
              oBugReport.atxMemoryRemarks.append(("Memory allocation start", oVirtualAllocation.uBaseAddress, None));
              oBugReport.atxMemoryRemarks.append(("Memory allocation end", oVirtualAllocation.uEndAddress, None));
            if oVirtualAllocation.bUnallocated:
              oBugReport.sBugTypeId = "AV%s@Unallocated" % sViolationTypeId;
              oBugReport.sBugDescription = "Access violation while %s unallocated memory at 0x%X." % \
                  (sViolationTypeDescription, uAccessViolationAddress);
              oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled or memory be allocate at the address.";
            elif oVirtualAllocation.bReserved:
              oBugReport.sBugTypeId = "AV%s@Reserved" % sViolationTypeId;
              oBugReport.sBugDescription = "Access violation at 0x%X while %s reserved but unallocated memory at 0x%X-0x%X." % \
                  (uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation.uBaseAddress, \
                  oVirtualAllocation.uBaseAddress + oVirtualAllocation.uSize);
              oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or " \
                  "memory be allocated at the address rather than reserved.";
            else:
              sMemoryProtectionsDescription = {
                0x01: "allocated but inaccessible", 0x02: "read-only",            0x04: "read- and writable",  0x08: "read- and writable",
                0x10: "executable",                 0x20: "read- and executable",
              }[oVirtualAllocation.uProtection];
              oBugReport.sBugTypeId = "AV%s@Arbitrary" % sViolationTypeId;
              oBugReport.sBugDescription = "Access violation while %s %s memory at 0x%X." % \
                  (sViolationTypeDescription, sMemoryProtectionsDescription, uAccessViolationAddress);
              oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or accessible memory be allocated the the address.";
              if oProcess.oCdbWrapper.bGenerateReportHTML:
                # Clamp size, potentially update start if size needs to shrink but end is not changed.
                uMemoryDumpStartAddress, uMemoryDumpSize = ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(
                  uAccessViolationAddress, oProcess.uPointerSize, oVirtualAllocation.uBaseAddress, oVirtualAllocation.uSize
                );
                oBugReport.fAddMemoryDump(
                  uMemoryDumpStartAddress,
                  uMemoryDumpStartAddress + uMemoryDumpSize,
                  "Memory near access violation at 0x%X" % uAccessViolationAddress,
                );
  
  oBugReport.sBugDescription += sViolationTypeNotes;
  return oBugReport;
