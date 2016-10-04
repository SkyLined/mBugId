import re;
from cBugReport import cBugReport;
from fsGetNumberDescription import fsGetNumberDescription;
from fsGetOffsetDescription import fsGetOffsetDescription;
from cCorruptionDetector import cCorruptionDetector;
from sBlockHTMLTemplate import sBlockHTMLTemplate;

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
          "Unknown VERIFIER STOP message line: %s\r\n%s" % (repr(sLine), "\r\n".join(asLines));
      break;
  else:
    assert uErrorNumber is None, \
        "Detected the start of a VERIFIER STOP message but not the end\r\n%s" % "\r\n".join(asLines);
    return False;
  if uErrorNumber == 0x303:
    # =======================================
    # VERIFIER STOP 0000000000000303: pid 0xB2C: NULL handle passed as parameter. A valid handle must be used.
    # 
    # 0000000000000000 : Not used.
    # 0000000000000000 : Not used.
    # 0000000000000000 : Not used.
    # 0000000000000000 : Not used.
    # 
    # =======================================
    # This is not interesting; do not report an error.
    return True;
  
  assert uHeapBlockAddress is not None, \
      "The heap block start address was not found in the verifier stop message.\r\n%s" % "\r\n".join(asRelevantLines);
  assert uHeapBlockSize is not None, \
      "The heap block size was not found in the verifier stop message.\r\n%s" % "\r\n".join(asRelevantLines);
  
  uHeapBlockEndAddress = uHeapBlockAddress + uHeapBlockSize;
  uHeapPageEndAddress = (uHeapBlockEndAddress | 0xFFF) + 1;
  assert uHeapPageEndAddress >= uHeapBlockEndAddress, \
      "The heap block at 0x%X is expected to end at 0x%X, but the page is expected to end at 0x%X, which is impossible.\r\n%s" % \
      (uHeapBlockAddress, uHeapBlockEndAddress, uHeapPageEndAddress, "\r\n".join(asRelevantLines));
  uMemoryDumpStartAddress = uHeapBlockAddress;
  uMemoryDumpSize = uHeapBlockSize;
  atxMemoryRemarks = [
    ("Memory block start", uHeapBlockAddress, None),
    ("Memory block end", uHeapBlockEndAddress, None)
  ];
  
  oCorruptionDetector = cCorruptionDetector(oCdbWrapper);
  # End of VERIFIER STOP message; report a bug.
  if sMessage in ["corrupted start stamp", "corrupted end stamp"]:
    assert uCorruptionAddress is None, \
        "We do not expect the corruption address to be provided in the VERIFIER STOP message\r\n%s" % \
            "\r\n".join(asRelevantLines);
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
            "\r\n".join(asRelevantLines);
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
            "\r\n".join(asRelevantLines);
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
  
  # See if we have a better idea of where the corruption started and ended:
  uCorruptionStartAddress = uCorruptionAddress;
  uCorruptionEndAddress = uCorruptionAddress;
  if oCorruptionDetector.bCorruptionDetected:
    uCorruptionStartAddress = oCorruptionDetector.uCorruptionStartAddress;
    uCorruptionEndAddress = oCorruptionDetector.uCorruptionEndAddress;
    uCorruptionSize = uCorruptionEndAddress - uCorruptionStartAddress;
    atxMemoryRemarks.append(("Corrupted memory", uCorruptionStartAddress, uCorruptionSize));
    assert uCorruptionAddress is None or uCorruptionAddress == oCorruptionDetector.uCorruptionStartAddress, \
        "Verifier reported corruption at address 0x%X but BugId detected corruption at address 0x%X\r\n%s" % \
        (uCorruptionAddress, oCorruptionDetector.uCorruptionStartAddress, "\r\n".join(asRelevantLines));
  else:
    oBugReport.atxMemoryRemarks.append(("Corrupted memory", uCorruptionAddress, None));
    uCorruptionStartAddress = uCorruptionAddress;
    uCorruptionEndAddress = uCorruptionAddress;
  
  # If the corruption starts before or ends after the heap block, expand the memory dump to include the entire
  # corrupted region.
  if uCorruptionStartAddress < uMemoryDumpStartAddress:
    uMemoryDumpSize += uMemoryDumpStartAddress - uCorruptionStartAddress;
    uMemoryDumpStartAddress = uCorruptionStartAddress;
  if uCorruptionEndAddress < uMemoryDumpStartAddress + uMemoryDumpSize:
    uMemoryDumpSize += uCorruptionEndAddress - (uMemoryDumpStartAddress + uMemoryDumpSize);
  # Get a human readable description of the start offset of corruption relative to the heap block, where corruption
  # starting before or inside the heap block will be relative to the start, and corruption after it to the end.
  uCorruptionStartOffset = uCorruptionStartAddress - uHeapBlockAddress;
  if uCorruptionStartOffset >= uHeapBlockSize:
    uCorruptionStartOffset -= uHeapBlockSize;
    sCorruptionStartOffsetDescription = "%d/0x%X bytes beyond" % (uCorruptionStartOffset, uCorruptionStartOffset);
    sBugTypeId += fsGetOffsetDescription(uCorruptionStartOffset);
  elif uCorruptionStartOffset > 0:
    sCorruptionStartOffsetDescription = "%d/0x%X bytes into" % (uCorruptionStartOffset, uCorruptionStartOffset);
    sBugTypeId += "@%s" % fsGetNumberDescription(uCorruptionStartOffset);
  else:
    sCorruptionStartOffsetDescription = "%d/0x%X bytes before" % (-uCorruptionStartOffset, -uCorruptionStartOffset);
    sBugTypeId += fsGetOffsetDescription(uCorruptionStartOffset);
  sBugDescription = "Page heap detected heap corruption at 0x%X; %s a %d/0x%X byte heap block at address 0x%X" % \
      (uCorruptionStartAddress, sCorruptionStartOffsetDescription, uHeapBlockSize, uHeapBlockSize, uHeapBlockAddress);
    
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
  oBugReport = cBugReport.foCreate(oCdbWrapper, sBugTypeId, sBugDescription, sSecurityImpact);
  oBugReport.atxMemoryDumps.append(("Heap block for memory corruption", uMemoryDumpStartAddress, uMemoryDumpSize));
  oBugReport.atxMemoryRemarks.extend(atxMemoryRemarks);
  sVerifierStopMessageHTML = sBlockHTMLTemplate % {
    "sName": "VERIFIER STOP message",
    "sContent": "<pre>%s</pre>" % "\r\n".join([oCdbWrapper.fsHTMLEncode(s) for s in asRelevantLines])
  };
  oBugReport.asExceptionSpecificBlocksHTML.append(sVerifierStopMessageHTML);
  
  oBugReport.bRegistersRelevant = False;
  oCdbWrapper.oBugReport = oBugReport;
  return True;
