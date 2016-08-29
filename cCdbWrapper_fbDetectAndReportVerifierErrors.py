import re;
from cBugReport import cBugReport;
from fsGetNumberDescription import fsGetNumberDescription;
from fsGetOffsetDescription import fsGetOffsetDescription;
from cCorruptionDetector import cCorruptionDetector;

def cCdbWrapper_fbDetectAndReportVerifierErrors(oCdbWrapper, asCdbOutput):
  uErrorNumber = None;
  uProcessId = None;
  sMessage = None;
  uHeapBlockAddress = None;
  uHeapBlockSize = None;
  uCorruptedStamp = None;
  uCorruptionAddress = None;
  asRelevantLines = [];

  for sLine in asCdbOutput:
    # Ignore exmpty lines
    if not sLine:
      continue;
    # Look for the first VERIFIER STOP message and gather information
    if uErrorNumber is None:
      oErrorMessageMatch = re.match(r"^VERIFIER STOP ([0-9A-F]+): pid 0x([0-9A-F]+): (.*?)\s*$", sLine);
      if oErrorMessageMatch:
        sErrorNumber, sProcessId, sMessage = oErrorMessageMatch.groups();
        uErrorNumber = long(sErrorNumber, 16);
        uProcessId = long(sProcessId, 16);
      asRelevantLines.append(sLine);
      continue;
    asRelevantLines.append(sLine);
    # A VERIFIER STOP message has been detected, gather what information verifier provides:
    oInformationMatch = re.match(r"\t([0-9A-F]+) : (.*?)\s*$", sLine);
    if oInformationMatch:
      sValue, sDescription = oInformationMatch.groups();
      uValue = long(sValue, 16);
      if sDescription == "Heap block": uHeapBlockAddress = uValue;
      elif sDescription == "Block size": uHeapBlockSize = uValue;
      elif sDescription == "Corrupted stamp": uCorruptedStamp = uValue;
      elif sDescription == "corruption address": uCorruptionAddress = uValue;
    else:
      assert sLine.strip().replace("=", "") == "", \
          "Unknown VERIFIER STOP message line: %s" % repr(sLine);
      break;
  else:
    assert uErrorNumber is None, \
        "Detected the start of a VERIFIER STOP message but not the end\r\n%s" % "\r\n".join(asLines);
    return False;
  
  uHeapBlockEndAddress = uHeapBlockAddress + uHeapBlockSize;
  uHeapPageEndAddress = (uHeapBlockEndAddress | 0xFFF) + 1;
  assert uHeapPageEndAddress >= uHeapBlockEndAddress, \
      "The heap block at 0x%X is expected to end at 0x%X, but the page is expected to end at 0x%X, which is impossible." % \
      (uHeapBlockAddress, uHeapBlockEndAddress, uHeapPageEndAddress);
  oCorruptionDetector = cCorruptionDetector(oCdbWrapper);
  # End of VERIFIER STOP message; report a bug.
  if sMessage in ["corrupted start stamp", "corrupted end stamp"]:
    assert uCorruptionAddress is None, \
        "We do not expect the corruption address to be provided in the VERIFIER STOP message";
    sBugTypeId = "OOBW";
    # Both the start and end stamp may have been corrupted and it appears that a bug in verifier causes a corruption
    # of the end stamp to be reported as a corruption of the start stamp, so we'll check both for unexpected values:
    uPointerSize = oCdbWrapper.fuGetValue("$ptrsize");
    if not oCdbWrapper.bCdbRunning: return;
    # https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
    uEndStampAddress = uHeapBlockAddress - uPointerSize;          # ULONG with optional padding to pointer size
    if uPointerSize == 8:
      # End stamp comes immediately after other header values
      oCorruptionDetector.fDetectCorruption(uEndStampAddress, 0, 0, 0, 0, [0xBA, 0xBB], 0xBB, 0xBA, 0xDC);
    else:
      oCorruptionDetector.fDetectCorruption(uEndStampAddress, [0xBA, 0xBB], 0xBB, 0xBA, 0xDC);
    uStackTraceAddress = uEndStampAddress - uPointerSize;         # PVOID
    uFreeQueueAddress = uStackTraceAddress - 2 * uPointerSize;    # LIST_ENTRY
    uActualSizeAddress = uFreeQueueAddress - uPointerSize;        # size_t
    uRequestedSizeAddress = uActualSizeAddress - uPointerSize;    # size_t
    uHeapAddressAddress = uRequestedSizeAddress - uPointerSize;   # PVOID
    uStartStampAddress = uHeapAddressAddress - uPointerSize;      # ULONG with optional padding to pointer size
    if uPointerSize == 8:
      # End stamp comes immediately before other header values
      oCorruptionDetector.fDetectCorruption(uStartStampAddress, [0xBA, 0xBB], 0xBB, 0xCD, 0xAB, 0, 0, 0, 0);
    else:
      oCorruptionDetector.fDetectCorruption(uStartStampAddress, [0xBA, 0xBB], 0xBB, 0xCD, 0xAB);
    assert oCorruptionDetector.bCorruptionDetected, \
        "Cannot find any sign of corruption";
  elif sMessage == "corrupted suffix pattern":
    assert uCorruptionAddress is not None, \
        "The corruption address is expected to be provided in the VERIFIER STOP message:\r\n%s" % \
            "\r\n" % (asRelevantLines);
    # Page heap stores the heap as close as possible to the edge of a page, taking into account that the start of the
    # heap block must be properly aligned. Bytes between the heap block and the end of the page are initialized to
    # 0xD0. Verifier has detected that one of the bytes changed value, which indicates an out-of-bounds write. BugId
    # will try to find all bytes that were changed:
    sBugTypeId = "OOBW";
    uPaddingSize = uHeapPageEndAddress - uHeapBlockEndAddress;
    oCorruptionDetector.fDetectCorruption(uHeapBlockEndAddress, *[0xD0 for x in xrange(uPaddingSize)]);
    assert oCorruptionDetector.bCorruptionDetected, \
        "Cannot find any sign of corruption";
  elif sMessage == "corrupted infix pattern":
    assert uCorruptionAddress is not None, \
        "The corruption address is expected to be provided in the VERIFIER STOP message:\r\n%s" % \
            "\r\n" % (asRelevantLines);
    # Page heap sometimes does not free a heap block immediately, but overwrites the bytes with 0xF0. Verifier has
    # detected that one of the bytes changed value, which indicates a write-after-free. BugId will try to find all
    # bytes that were changed:
    sBugTypeId = "UAFW";
    oCorruptionDetector.fDetectCorruption(uHeapBlockAddress, *[0xF0 for x in xrange(uHeapBlockSize)]);
    assert oCorruptionDetector.bCorruptionDetected, \
        "Cannot find any sign of corruption";
  else:
    sBugTypeId = "HeapCorrupt";
  if uHeapBlockSize is not None:
    sBugTypeId += "[%s]" % (fsGetNumberDescription(uHeapBlockSize));
  if oCorruptionDetector.bCorruptionDetected:
    if uCorruptionAddress is None:
      uCorruptionAddress = oCorruptionDetector.uCorruptionStartAddress;
    else:
      assert uCorruptionAddress == oCorruptionDetector.uCorruptionStartAddress, \
          "Verifier reported corruption at address 0x%X but BugId detected corruption at address 0x%X" % \
          (uCorruptionAddress, oCorruptionDetector.uCorruptionStartAddress);
  if uCorruptionAddress is not None:
    sMessage = "heap corruption";
    uCorruptionOffset = uCorruptionAddress - uHeapBlockAddress;
    if uCorruptionOffset >= uHeapBlockSize:
      uCorruptionOffset -= uHeapBlockSize;
      sOffsetDescription = "%d/0x%X bytes beyond" % (uCorruptionOffset, uCorruptionOffset);
      sBugTypeId += fsGetOffsetDescription(uCorruptionOffset);
    elif uCorruptionOffset > 0:
      sOffsetDescription = "%d/0x%X bytes into" % (uCorruptionOffset, uCorruptionOffset);
      sBugTypeId += "@%s" % fsGetNumberDescription(uCorruptionOffset);
    else:
      sOffsetDescription = "%d/0x%X bytes before" % (-uCorruptionOffset, -uCorruptionOffset);
      sBugTypeId += fsGetOffsetDescription(uCorruptionOffset);
    sBugDescription = "Page heap detected %s at 0x%X; %s a %d/0x%X byte heap block at address 0x%X" % \
        (sMessage, uCorruptionAddress, sOffsetDescription, uHeapBlockSize, uHeapBlockSize, uHeapBlockAddress);
    uRelevantAddress = uCorruptionAddress;
  else:
    sBugDescription = "Page heap detected %s in a %d/0x%X byte heap block at address 0x%X." % \
        (sMessage, uHeapBlockSize, uHeapBlockSize, uHeapBlockAddress);
    uRelevantAddress = uHeapBlockAddress;
  
  # If we detected corruption by scanning certain bytes in the applications memory, make sure this matches what
  # verifier reported and save all bytes that were affected: so far, we only saved the bytes that had an unexpected
  # value, but there is a chance that a byte was overwritten with the same value it has before, in which case it was
  # not saved. This can be detect if it is surrounded by bytes that did change value. This code reads the value of all
  # bytes between the first and last byte that we detected was corrupted:
  asCorruptedBytes = oCorruptionDetector.fasCorruptedBytes();
  if asCorruptedBytes:
    sBugDescription += " The following byte values were written to the corrupted area: %s." % ", ".join(asCorruptedBytes);
    sBugTypeId += oCorruptionDetector.fsCorruptionId() or "";
  
  sSecurityImpact = "Potentially exploitable security issue, if the corruption is attacker controlled";
  oCdbWrapper.oBugReport = cBugReport.foCreate(oCdbWrapper, sBugTypeId, sBugDescription, sSecurityImpact);
  oCdbWrapper.oBugReport.duRelevantAddress_by_sDescription \
      ["memory corruption at 0x%X" % uRelevantAddress] = uRelevantAddress;
  oCdbWrapper.oBugReport.bRegistersRelevant = False;
  return True;
