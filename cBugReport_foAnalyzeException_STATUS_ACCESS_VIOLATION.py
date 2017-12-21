import re, struct;
from cThreadEnvironmentBlock import cThreadEnvironmentBlock;
from dxConfig import dxConfig;
from fsGetNumberDescription import fsGetNumberDescription;
from ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from fSetBugReportPropertiesForAccessViolationUsingHeapManagerData import fSetBugReportPropertiesForAccessViolationUsingHeapManagerData;
from mWindowsAPI import cVirtualAllocation, oSystemInfo;
from sBlockHTMLTemplate import sBlockHTMLTemplate;

ddtsDetails_uSpecialAddress_sISA = {
  # There are a number of values that are very close to eachother, and because an offset is likely to be added when
  # reading using a pointer, having all of them here does not offer extra information. So, I've limited it to values
  # that are sufficiently far away from eachother to be recognisable after adding offsets.
  "x86": {              # Id                      Description                                           Security impact
            # https://en.wikipedia.org/wiki/Magic_number_(programming)#Magic_debug_values
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
  oCdbWrapper = oProcess.oCdbWrapper;
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
  
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, uAccessViolationAddress);
  
  # Try handling this as a NULL pointer, which is special cased because we do not always report these.
  if fbAccessViolationIsNULLPointer(
    oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
  ):
    if dxConfig["bIgnoreFirstChanceNULLPointerAccessViolations"] and not oException.bApplicationCannotHandleException:
      # This is a first chance exception; let the application handle it first.
      return None;
  else:
    # Try various ways of handling this AV:
    for fbAccessViolationHandled in [
      fbAccessViolationIsCollateralPoisonPointer,
      fbAccessViolationIsHeapManagerPointer,
      fbAccessViolationIsStackPointer,
      fbAccessViolationIsSpecialPointer,
      fbAccessViolationIsAllocatedPointer,
      fbAccessViolationIsReservedPointer,
      fbAccessViolationIsFreePointer,
      fbAccessViolationIsInvalidPointer,
    ]:
      if fbAccessViolationHandled(
        oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
      ):
        # Once it's handled, stop trying other handlers
        break;
    else:
      # Unable to handle (should not be possible!)
      raise AssertionError("Could not handle AV%s@0x%08X" % (sViolationTypeId, uAccessViolationAddress));
  oBugReport.sBugDescription += sViolationTypeNotes;
  return oBugReport;

def fbAccessViolationIsNULLPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  if uAccessViolationAddress == 0:
    sOffset = "";
  elif uAccessViolationAddress < oSystemInfo.uAllocationAddressGranularity:
    sOffset = "+%s" % fsGetNumberDescription(uAccessViolationAddress, "+");
  else:
    uAccessViolationNegativeOffset = {"x86": 1 << 32, "x64": 1 << 64}[oProcess.sISA] - uAccessViolationAddress;
    if uAccessViolationNegativeOffset >= oSystemInfo.uAllocationAddressGranularity:
      return False;
    sOffset = "-%s" % fsGetNumberDescription(uAccessViolationNegativeOffset, "-");
  oBugReport.sBugTypeId = "AV%s@NULL%s" % (sViolationTypeId, sOffset);
  oBugReport.sBugDescription = "Access violation while %s memory at 0x%X using a NULL pointer." % \
      (sViolationTypeDescription, uAccessViolationAddress);
  oBugReport.sSecurityImpact = None;
  # You normally cannot allocate memory at address 0, so it is impossible for an exploit to avoid this exception.
  # Therefore there is no collateral bug handling.
  return True;

def fbAccessViolationIsSpecialPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  dtsDetails_uSpecialAddress = ddtsDetails_uSpecialAddress_sISA[oProcess.sISA];
  for (uSpecialAddress, (sSpecialAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
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
      oBugReport.sBugDescription = "Access violation while %s memory at 0x%X using %s." % \
        (sViolationTypeDescription, uAccessViolationAddress, sAddressDescription);
      oBugReport.sSecurityImpact = sSecurityImpact;
      oCdbWrapper.oCollateralBugHandler.fSetExceptionHandler(lambda oCollateralBugHandler:
        fbAccessViolationExceptionHandler(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
      );
      return True;
  return False;

def fbAccessViolationIsCollateralPoisonPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  iOffset = oCdbWrapper.oCollateralBugHandler.fiGetOffsetForPoisonedAddress(oProcess, uAccessViolationAddress);
  if iOffset is None:
    # This is not near the poisoned address used by collateral
    return False;
  sSign = iOffset < 0 and "-" or "+";
  sOffset = "%s%s" % (sSign, fsGetNumberDescription(abs(iOffset), sSign));
  oBugReport.sBugTypeId = "AV%s@Poison%s" % (sViolationTypeId, sOffset);
  oBugReport.sBugDescription = "Access violation while %s memory at 0x%X using a poisoned value provided by cBugId." % \
    (sViolationTypeDescription, uAccessViolationAddress);
  oBugReport.sSecurityImpact = "Highly likely to be an exploitable security issue if your exploit can poison this value.";
  oCdbWrapper.oCollateralBugHandler.fSetExceptionHandler(lambda oCollateralBugHandler:
    fbAccessViolationExceptionHandler(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;

def fbAccessViolationIsHeapManagerPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  # This is not a special marker or NULL, so it must be some corrupt pointer
  # Get information about the memory region:
  oHeapManagerData = oProcess.foGetHeapManagerDataForAddress(uAccessViolationAddress);
  if not oHeapManagerData:
    return False;
  oBugReport.atxMemoryRemarks.extend(oHeapManagerData.fatxMemoryRemarks());
  fSetBugReportPropertiesForAccessViolationUsingHeapManagerData(
    oBugReport, \
    uAccessViolationAddress, sViolationTypeId, sViolationTypeDescription, \
    oHeapManagerData, \
    oProcess.oCdbWrapper.bGenerateReportHTML,
  );
  if (
    sViolationTypeDescription == "R" and \
    oHeapManagerData.oVirtualAllocation and \
    oHeapManagerData.oVirtualAllocation.bAllocated and \
    uAccessViolationAddress >= oHeapManagerData.uHeapBlockStartAddress and \
    uAccessViolationAddress < oHeapManagerData.uHeapBlockEndAddress
  ):
    uPointerSizedValue = oHeapManagerData.oVirtualAllocation.fuReadValueForOffsetAndSize(
      uAccessViolationAddress - oHeapManagerData.uHeapBlockStartAddress,
      oProcess.uPointerSize,
    );
  else:
    uPointerSizedValue = None;
  oCdbWrapper.oCollateralBugHandler.fSetExceptionHandler(lambda oCollateralBugHandler:
    fbAccessViolationExceptionHandler(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId, uPointerSizedValue = uPointerSizedValue)
  );
  return True;

def fbAccessViolationIsInvalidPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  # See if the address is valid:
  if not oVirtualAllocation.bInvalid:
    return False;
  oBugReport.sBugTypeId = "AV%s@Invalid" % sViolationTypeId;
  oBugReport.sBugDescription = "Access violation while %s memory at invalid address 0x%X." % (sViolationTypeDescription, uAccessViolationAddress);
  oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled.";
  # You normally cannot allocate memory at an invalid address, so it is impossible for an exploit to avoid this
  # exception. Therefore there is no collateral bug handling.
  return True;

def fbAccessViolationIsStackPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  # See if the address is near the stack for the current thread:
  oThreadEnvironmentBlock = cThreadEnvironmentBlock.foCreateForCurrentThread(oProcess);
  uOffsetFromTopOfStack = uAccessViolationAddress - oThreadEnvironmentBlock.uStackTopAddress;
  uOffsetFromBottomOfStack = oThreadEnvironmentBlock.uStackBottomAddress - uAccessViolationAddress;
  if uOffsetFromTopOfStack >= 0 and uOffsetFromTopOfStack <= oProcess.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromTopOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes passed the top of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromTopOfStack, uOffsetFromTopOfStack, oThreadEnvironmentBlock.uStackTopAddress);
  elif uOffsetFromBottomOfStack >= 0 and uOffsetFromBottomOfStack <= oProcess.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromBottomOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes before the bottom of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromBottomOfStack, uOffsetFromBottomOfStack, oThreadEnvironmentBlock.uStackTopAddress);
  else:
    return False;
  oBugReport.sSecurityImpact = "Potentially exploitable security issue.";
  oCdbWrapper.oCollateralBugHandler.fSetExceptionHandler(lambda oCollateralBugHandler:
    fbAccessViolationExceptionHandler(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;

def fbAccessViolationIsReservedPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  if not oVirtualAllocation.bReserved:
    return False;
  # No memory is allocated in this area, but is is reserved
  oBugReport.sBugTypeId = "AV%s@Reserved" % sViolationTypeId;
  oBugReport.sBugDescription = "Access violation at 0x%X while %s reserved but unallocated memory at 0x%X-0x%X." % \
      (uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation.uStartAddress, \
      oVirtualAllocation.uStartAddress + oVirtualAllocation.uSize);
  oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or " \
      "memory be allocated at the address rather than reserved.";
  oCdbWrapper.oCollateralBugHandler.fSetExceptionHandler(lambda oCollateralBugHandler:
    fbAccessViolationExceptionHandler(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;

def fbAccessViolationIsFreePointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  if not oVirtualAllocation.bFree:
    return False;
  # No memory is allocated in this area
  oBugReport.sBugTypeId = "AV%s@Unallocated" % sViolationTypeId;
  oBugReport.sBugDescription = "Access violation while %s unallocated memory at 0x%X." % (sViolationTypeDescription, uAccessViolationAddress);
  oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or memory be allocated at the address.";
  oCdbWrapper.oCollateralBugHandler.fSetExceptionHandler(lambda oCollateralBugHandler:
    fbAccessViolationExceptionHandler(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;

def fbAccessViolationIsAllocatedPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  if not oVirtualAllocation.bAllocated:
    return False;
  # Memory is allocated in this area, but apparantly not accessible in the way the code tried to.
  if oCdbWrapper.bGenerateReportHTML:
    oBugReport.atxMemoryRemarks.append(("Memory allocation start", oVirtualAllocation.uStartAddress, None));
    oBugReport.atxMemoryRemarks.append(("Memory allocation end", oVirtualAllocation.uEndAddress, None));
  sMemoryProtectionsDescription = {
    0x01: "allocated but inaccessible", 0x02: "read-only",            0x04: "read- and writable",  0x08: "read- and writable",
    0x10: "executable",                 0x20: "read- and executable",
  }[oVirtualAllocation.uProtection];
  oBugReport.sBugTypeId = "AV%s@Arbitrary" % sViolationTypeId;
  oBugReport.sBugDescription = "Access violation while %s %s memory at 0x%X." % \
      (sViolationTypeDescription, sMemoryProtectionsDescription, uAccessViolationAddress);
  oBugReport.sSecurityImpact = "Potentially exploitable security issue, if the address can be controlled, or accessible memory be allocated the the address.";
  # Add a memory dump
  if oCdbWrapper.bGenerateReportHTML:
    # Clamp size, potentially update start if size needs to shrink but end is not changed.
    uMemoryDumpStartAddress, uMemoryDumpSize = ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(
      uAccessViolationAddress, oProcess.uPointerSize, oVirtualAllocation.uStartAddress, oVirtualAllocation.uSize
    );
    oBugReport.fAddMemoryDump(
      uMemoryDumpStartAddress,
      uMemoryDumpStartAddress + uMemoryDumpSize,
      "Memory near access violation at 0x%X" % uAccessViolationAddress,
    );
  # You normally cannot modify the access rights of memory, so it is impossible for an exploit to avoid this exception.
  # Therefore there is no collateral bug handling. Note that if you can control the address you may be able to point
  # it somewhere that is accessible, e.g. this was some data that got interpreted as a pointer that happened to point
  # to memory that was not accessible, but the data is under attackers control. However, I have decide to assume the
  # exception cannot be avoided.
  return True;

duSizeInBits_by_sRegisterName = {
  "rax": 64,  "eax": 32,   "ax": 16, "ah": 8,  "al": 8,
  "rbx": 64,  "ebx": 32,   "bx": 16, "bh": 8,  "bl": 8,
  "rcx": 64,  "ecx": 32,   "cx": 16, "ch": 8,  "cl": 8,
  "rdx": 64,  "edx": 32,   "dx": 16, "dh": 8,  "dl": 8,
  "rsi": 64,  "esi": 32,   "si": 16,          "sil": 8,
  "rdi": 64,  "edi": 32,   "di": 16,          "dil": 8,
  "rbp": 64,  "ebp": 32,   "bp": 16,          "bpl": 8,
  "rsp": 64,  "esp": 32,   "sp": 16,          "spl": 8,
  "rip": 64,  "eip": 32,   "ip": 16,
   "r8": 64,  "r8d": 32,  "r8w": 16,          "r8b": 8,
   "r9": 64,  "r9d": 32,  "r9w": 16,          "r9b": 8,
  "r10": 64, "r10d": 32, "r10w": 16,         "r10b": 8,
  "r11": 64, "r11d": 32, "r11w": 16,         "r11b": 8,
  "r12": 64, "r12d": 32, "r12w": 16,         "r12b": 8,
  "r13": 64, "r13d": 32, "r13w": 16,         "r13b": 8,
  "r14": 64, "r14d": 32, "r14w": 16,         "r14b": 8,
  "r15": 64, "r15d": 32, "r15w": 16,         "r15b": 8,
    "mm0":  64,   "mm1":  64,   "mm2":  64,   "mm3":  64,   "mm4":  64,   "mm5":  64,  "mm6":   64,  "mm7":   64,
   "xmm0": 128,  "xmm1": 128,  "xmm2": 128,  "xmm3": 128,  "xmm4": 128,  "xmm5": 128,  "xmm6": 128,  "xmm7": 128,
   "xmm8": 128,  "xmm9": 128, "xmm10": 128, "xmm11": 128, "xmm12": 128, "xmm13": 128, "xmm14": 128, "xmm15": 128,
  "xmm16": 128, "xmm17": 128, "xmm18": 128, "xmm19": 128, "xmm20": 128, "xmm21": 128, "xmm22": 128, "xmm23": 128,
  "xmm24": 128, "xmm25": 128, "xmm26": 128, "xmm27": 128, "xmm28": 128, "xmm29": 128, "xmm30": 128, "xmm31": 128, 
   "ymm0": 256,  "ymm1": 256,  "ymm2": 256,  "ymm3": 256,  "ymm4": 256,  "ymm5": 256,  "ymm6": 256,  "ymm7": 256,
   "ymm8": 256,  "ymm9": 256, "ymm10": 256, "ymm11": 256, "ymm12": 256, "ymm13": 256, "ymm14": 256, "ymm15": 256,
  "ymm16": 256, "ymm17": 256, "ymm18": 256, "ymm19": 256, "ymm20": 256, "ymm21": 256, "ymm22": 256, "ymm23": 256,
  "ymm24": 256, "ymm25": 256, "ymm26": 256, "ymm27": 256, "ymm28": 256, "ymm29": 256, "ymm30": 256, "ymm31": 256, 
};
gduSizeInBits_by_sPointerType = {
  "byte": 8, "word": 16, "dword": 32, "qword": 64, "mmword": 64, "xmmword": 128, "ymmword": 256,
}
  
def fbAccessViolationExceptionHandler(oCollateralBugHandler, oCdbWrapper, uProcessId, sViolationTypeId, uPointerSizedValue = None):
  # I could just pass the oProcess, as there is no code execution between when the exception handler was set and called,
  # but if that changes in the future, this.
  oProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
  # See if we can fake execution of the current instruction, so we can continue the application as if it had been
  # executed without actually executing it.
  asUnassembleOutput = oProcess.fasExecuteCdbCommand(
    sCommand = "u @$ip L2", 
    sComment = "Get information about the instruction that caused the AV",
  );
  oCurrentInstructionMatch = len(asUnassembleOutput) == 3 and \
      re.match(r"^[0-9`a-f]+\s+[0-9`a-f]+\s+(\w+)(?:\s+(.*))?$", asUnassembleOutput[1], re.I);
  oNextInstructionMatch = len(asUnassembleOutput) == 3 and \
      re.match(r"^([0-9`a-f]+)\s+[0-9`a-f]+\s+\w+(?:\s+.*)?$", asUnassembleOutput[2], re.I);
  assert oCurrentInstructionMatch, \
      "Unrecognised unassemble output second line:\r\n%s" % "\r\n".join(asUnassembleOutput);
  assert oNextInstructionMatch, \
      "Unrecognised unassemble output third line:\r\n%s" % "\r\n".join(asUnassembleOutput);
  (sCurrentInstructionName, sCurrentInstructionArguments) = oCurrentInstructionMatch.groups();
  (sNextInstructionAddress,) = oNextInstructionMatch.groups();
  uNextInstructionAddress = long(sNextInstructionAddress.replace("`", ""), 16);
  if sCurrentInstructionName in ["add", "addsd", "mov", "movzx", "movsd", "mulsd", "sub", "subsd"]:
    # We do not care about the difference between these operations; for writes, we simply discard the value. For reads
    # we assume that we have full control over the memory at the specified address, and thus full control over the
    # result stored in the register, so we just fake reading a poisoned value.
    asCurrentInstructionArguments = sCurrentInstructionArguments.split(",");
    assert len(asCurrentInstructionArguments) == 2, \
        "Instruction on line 2 appears to have %d arguments instead of 2:\r\n%s" % \
        (len(asCurrentInstructionArguments), "\r\n".join(asUnassembleOutput));
    sInstructionPointerRegister = {"x86": "eip", "x64": "rip"}[oProcess.sISA];
    if sViolationTypeId == "R":
      # We fake read AVs that read memory into a register by setting that register to a poisoned value and advancing
      # the instruction pointer to the next instruction.
      sDestinationRegister = asCurrentInstructionArguments[0];
      uDestinationSizeInBits = duSizeInBits_by_sRegisterName[sDestinationRegister];
      assert uDestinationSizeInBits is not None, \
          "Unrecognised `mov` instruction first/destination argument (expected register, got %s):\r\n%s" % \
          (sDestinationRegister, "\r\n".join(asUnassembleOutput));
      oSourceArgumentMatch = re.match("^(byte|(?:d|q|[xy]?(mm))?word) ptr \[.*\]$", asCurrentInstructionArguments[1]);
      assert oSourceArgumentMatch, \
          "Unrecognized `mov` instruction second/source argument (expected `... ptr [...]`, got %s):\r\n%s" % \
          (asCurrentInstructionArguments[1], "\r\n".join(asUnassembleOutput));
      sPointerType, bIsMMPointer = oSourceArgumentMatch.groups();
      uSourceSizeInBits = gduSizeInBits_by_sPointerType[sPointerType];
      if not bIsMMPointer:
        uPoisonValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, uSourceSizeInBits, uPointerSizedValue);
#        print "Faked read %d bits (0x%X) into %d bits %s" % (uSourceSize, uPoisonValue, uDestinationSizeInBits, sDestinationRegister);
        asSpoofInstructionOutput = oProcess.fasExecuteCdbCommand(
          sCommand = "r @%s=0x%X,@%s=0x%X,@%s,@%s;" % (
            sDestinationRegister, uPoisonValue,
            sInstructionPointerRegister, uNextInstructionAddress,
            sDestinationRegister, sInstructionPointerRegister,
          ),
          sComment = "Fake and skip instruction that caused the read AV",
        );
      else:
        # This is a bit more involved, as we can only set entire MM registers using 4 floating point numbers and we
        # want to set it to one or more pointer sized integers, which may mean we only want to set part of the register.
        if uSourceSizeInBits != uDestinationSizeInBits:
          # We want to write only part of the register: read the current value so we can preserve part of it.
          asGetDestinationBytesOutput = oProcess.fasExecuteCdbCommand(
            sCommand = "r @%s:%dub;" % (sDestinationRegister, uDestinationSizeInBits / 8),
            sComment = "Get current value of register",
          );
#          print "asGetDestinationBytesOutput: %s" % repr(asGetDestinationBytesOutput);
          assert len(asGetDestinationBytesOutput) == 1 and asGetDestinationBytesOutput[0].startswith("%s=" % sDestinationRegister), \
              "Unexpected register value output:\r\n%s" % "\r\n".join(asGetDestinationBytesOutput);
          auDestinationRegisterBytes = [long(s, 16) for s in asGetDestinationBytesOutput[0].split("=", 1)[1].split(" ") if s];
          auDestinationRegisterBytes.reverse();
        else:
          # Everything will be overwritten.
          auDestinationRegisterBytes = [0 for x in xrange(uDestinationSizeInBits / 8)];
#        print "auDestinationRegisterBytes: %s" % repr(auDestinationRegisterBytes);
        # We will fake read as many pointer sized values from the collateral poison value queue as will fit in the
        # source value.
        uPointerSizeInBits = oProcess.uPointerSize * 8;
        uSourceSizeInPointers = uSourceSizeInBits / uPointerSizeInBits;
        uIndex = 0;
        for x in xrange(uSourceSizeInPointers):
          uPoisonValue = oCollateralBugHandler.fuGetPoisonedValue(oProcess, uPointerSizeInBits, uPointerSizedValue);
          # The bytes in this poison value are written to the destination register buffer.
          for y in xrange(uPointerSizeInBits / 8):
            auDestinationRegisterBytes[uIndex] = uPoisonValue & 0xFF;
            uPoisonValue >>= 8;
            uIndex += 1;
#        print "auDestinationRegisterBytes: %s" % repr(auDestinationRegisterBytes);
        # We now know the bytes we want in the destination register, but we can only set it as 4 float values. So we
        # will convert these bytes to four floats:
        sDestinationRegisterBytes = "".join([chr(uByte) for uByte in auDestinationRegisterBytes]);
        uFloatSizeInBits = uDestinationSizeInBits / 4;
        anDestinationRegisterFloats = struct.unpack(">%s" % ({32: "f", 64: "d"}[uFloatSizeInBits] * 4), sDestinationRegisterBytes);
#        print "anDestinationRegisterFloats: %s" % repr(anDestinationRegisterFloats);
        sDestinationRegisterFloats = " ".join(["%f" % nFloat for nFloat in anDestinationRegisterFloats]);
        # Overwrite the register to fake a read instruction and update the instruction pointer to the next instruction.
        asSpoofInstructionOutput = oProcess.fasExecuteCdbCommand(
          sCommand = "r @%s=%s,@%s=0x%X,@%s,@%s;" % (
            sDestinationRegister, sDestinationRegisterFloats,
            sInstructionPointerRegister, uNextInstructionAddress,
            sDestinationRegister, sInstructionPointerRegister,
          ),
          sComment = "Fake and skip instruction that caused the read AV",
        );
#        print "asSpoofInstructionOutput: %s" % repr(asSpoofInstructionOutput);
    else:
      # We fake write AVs that write a register to memory by advancing the instruction pointer to the next
      # instruction.
      asSpoofInstructionOutput = oProcess.fasExecuteCdbCommand(
        sCommand = "r @%s=0x%X;" % (sInstructionPointerRegister, uNextInstructionAddress),
        sComment = "Skip instruction that caused the write AV",
      );
    return True;
  else:
    return False;
