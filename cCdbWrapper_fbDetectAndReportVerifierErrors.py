import re;
from cBugReport import cBugReport;
from cPageHeapReport import cPageHeapReport;
from fsGetNumberDescription import fsGetNumberDescription;
from fsGetOffsetDescription import fsGetOffsetDescription;
from cCorruptionDetector import cCorruptionDetector;
from sBlockHTMLTemplate import sBlockHTMLTemplate;

def cCdbWrapper_fbDetectAndReportVerifierErrors(oCdbWrapper, asCdbOutput):
  uErrorNumber = None;
  uProcessId = None;
  sMessage = None;
  uVerifierStopHeapBlockStartAddress = None;
  uVerifierStopHeapBlockSize = None;
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
    # A VERIFIER STOP message has been detected, gather what information verifier provides:
    oInformationMatch = re.match(r"\t([0-9A-F]+) : (.*?)\s*$", sLine);
    if oInformationMatch:
      asRelevantLines.append(sLine);
      sValue, sDescription = oInformationMatch.groups();
      uValue = long(sValue, 16);
      if sDescription == "Heap block": uVerifierStopHeapBlockStartAddress = uValue;
      elif sDescription == "Block size": uVerifierStopHeapBlockSize = uValue;
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
  
  assert uVerifierStopHeapBlockStartAddress is not None, \
      "The heap block start address was not found in the verifier stop message.\r\n%s" % "\r\n".join(asRelevantLines);
  assert uVerifierStopHeapBlockSize is not None, \
      "The heap block size was not found in the verifier stop message.\r\n%s" % "\r\n".join(asRelevantLines);
  
  oCorruptionDetector = cCorruptionDetector(oCdbWrapper);
  oPageHeapReport = cPageHeapReport.foCreate(oCdbWrapper, uVerifierStopHeapBlockStartAddress);
  if not oCdbWrapper.bCdbRunning: return None;
  if oPageHeapReport:
    # Prefer page heap information over VERIFIER STOP info - the later has been known to be incorrect sometimes, for
    # instance when the application frees (heap pointer + offset), the VERIFIER STOP info will use that as the heap
    # block base, whereas the page heap report will correctly report (heap pointer) as the heap block base.
    uAllocationStartAddress = oPageHeapReport.uAllocationStartAddress;
    uAllocationEndAddress = oPageHeapReport.uAllocationEndAddress;
    # Check the page heap data near the heap block for signs of corruption:
    oPageHeapReport.fbCheckForCorruption(oCorruptionDetector);
    if not oCdbWrapper.bCdbRunning: return None;
  if oPageHeapReport and oPageHeapReport.uBlockStartAddress:
    uHeapBlockStartAddress = oPageHeapReport.uBlockStartAddress;
    uHeapBlockSize = oPageHeapReport.uBlockSize;
    uHeapBlockEndAddress = uHeapBlockStartAddress + uHeapBlockSize;
  else:
    uHeapBlockStartAddress = uVerifierStopHeapBlockStartAddress;
    uHeapBlockSize = uVerifierStopHeapBlockSize;
    uHeapBlockEndAddress = uVerifierStopHeapBlockStartAddress + uVerifierStopHeapBlockSize;
  atxMemoryRemarks = [];
  if oCdbWrapper.bGenerateReportHTML:
    uMemoryDumpStartAddress = uHeapBlockStartAddress;
    uMemoryDumpSize = uVerifierStopHeapBlockSize;
    if oPageHeapReport:
      atxMemoryRemarks.extend(oPageHeapReport.fatxMemoryRemarks());
  
  # Handle various VERIFIER STOP messages.
  sBugDescription = None;
  if sMessage in ["corrupted start stamp", "corrupted end stamp"]:
    assert uCorruptionAddress is None, \
        "We do not expect the corruption address to be provided in this VERIFIER STOP message\r\n%s" % \
            "\r\n".join(asRelevantLines);
    if not oCorruptionDetector.bCorruptionDetected and uHeapBlockStartAddress != uVerifierStopHeapBlockStartAddress:
      # When the application attempts to free (heap pointer + offset), Verifier does not detect this and will assume
      # the application provided pointer is correct. This causes it to look for the start and end stamp in the wrong
      # location and report this bug as memory corruption. When the page heap data shows no signs of corruption, we
      # can special case it.
      iFreeAtOffset = uVerifierStopHeapBlockStartAddress - uHeapBlockStartAddress;
      sBugTypeId = "MisalignedFree[%s]%s" % (fsGetNumberDescription(uHeapBlockSize), fsGetOffsetDescription(iFreeAtOffset));
      sOffsetBeforeOrAfter = iFreeAtOffset < 0 and "before" or "after";
      sBugDescription = "The application attempted to free memory using a pointer that was %d/0x%X bytes %s a " \
          "%d/0x%X byte heap block at address 0x%X" % (abs(iFreeAtOffset), abs(iFreeAtOffset), \
          sOffsetBeforeOrAfter, uHeapBlockSize, uHeapBlockSize, uHeapBlockStartAddress);
      sSecurityImpact = "Unknown: this type of bug has not been analyzed before";
    else:
      sBugTypeId = "OOBW[%s]" % (fsGetNumberDescription(uHeapBlockSize));
      assert oCorruptionDetector.bCorruptionDetected, \
          "Cannot find any sign of corruption";
  elif sMessage == "corrupted suffix pattern":
    assert uCorruptionAddress is not None, \
        "The corruption address is expected to be provided in this VERIFIER STOP message:\r\n%s" % \
            "\r\n".join(asRelevantLines);
    # Page heap stores the heap as close as possible to the edge of a page, taking into account that the start of the
    # heap block must be properly aligned. Bytes between the heap block and the end of the page are initialized to
    # 0xD0. Verifier has detected that one of the bytes changed value, which indicates an out-of-bounds write. BugId
    # will try to find all bytes that were changed:
    sBugTypeId = "OOBW[%s]" % (fsGetNumberDescription(uHeapBlockSize));
    assert oCorruptionDetector.bCorruptionDetected, \
        "Cannot find any sign of corruption";
  elif sMessage == "corrupted infix pattern":
    assert uCorruptionAddress is not None, \
        "The corruption address is expected to be provided in the VERIFIER STOP message:\r\n%s" % \
            "\r\n".join(asRelevantLines);
    # Page heap sometimes does not free a heap block immediately, but overwrites the bytes with 0xF0. Verifier has
    # detected that one of the bytes changed value, which indicates a write-after-free. BugId will try to find all
    # bytes that were changed:
    sBugTypeId = "UAFW[%s]" % (fsGetNumberDescription(uHeapBlockSize));
    # TODO add these checks to cPaheHeapReport if possible.
    oCorruptionDetector.fbDetectCorruption(uHeapBlockStartAddress, [0xF0 for x in xrange(uHeapBlockSize)]);
    assert oCorruptionDetector.bCorruptionDetected, \
        "Cannot find any sign of corruption";
  else:
    sBugTypeId = "HeapCorrupt[%s]" % (fsGetNumberDescription(uHeapBlockSize));
  # sBugDescription is not set if this is a memory corruption
  
  # See if we have a better idea of where the corruption started and ended:
  if oCorruptionDetector.bCorruptionDetected:
    uCorruptionStartAddress = oCorruptionDetector.uCorruptionStartAddress;
    uCorruptionEndAddress = oCorruptionDetector.uCorruptionEndAddress;
    uCorruptionSize = uCorruptionEndAddress - uCorruptionStartAddress;
    if oCdbWrapper.bGenerateReportHTML:
      atxMemoryRemarks.extend(oCorruptionDetector.fatxMemoryRemarks());
    assert uCorruptionAddress is None or uCorruptionAddress == oCorruptionDetector.uCorruptionStartAddress, \
        "Verifier reported corruption at address 0x%X but BugId detected corruption at address 0x%X\r\n%s" % \
        (uCorruptionAddress, oCorruptionDetector.uCorruptionStartAddress, "\r\n".join(asRelevantLines));
    bCorruptionDetected = True;
  elif uCorruptionAddress:
    if oCdbWrapper.bGenerateReportHTML:
      atxMemoryRemarks.append(("Corrupted memory", uCorruptionAddress, None));
    uCorruptionStartAddress = uCorruptionAddress;
    uCorruptionEndAddress = uCorruptionAddress;
    bCorruptionDetected = True;
  else:
    bCorruptionDetected = False;
  
  if bCorruptionDetected:
    # If the corruption starts before or ends after the heap block, expand the memory dump to include the entire
    # corrupted region.
    if oCdbWrapper.bGenerateReportHTML:
      if uCorruptionStartAddress < uMemoryDumpStartAddress:
        uMemoryDumpSize += uMemoryDumpStartAddress - uCorruptionStartAddress;
        uMemoryDumpStartAddress = uCorruptionStartAddress;
      if uCorruptionEndAddress < uMemoryDumpStartAddress + uMemoryDumpSize:
        uMemoryDumpSize += uCorruptionEndAddress - (uMemoryDumpStartAddress + uMemoryDumpSize);
    # Get a human readable description of the start offset of corruption relative to the heap block, where corruption
    # starting before or inside the heap block will be relative to the start, and corruption after it to the end.
    uCorruptionStartOffset = uCorruptionStartAddress - uHeapBlockStartAddress;
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
        (uCorruptionStartAddress, sCorruptionStartOffsetDescription, uHeapBlockSize, uHeapBlockSize, uHeapBlockStartAddress);
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
  else:
    assert sBugDescription, \
        "sBugDescription should have been set";
    
  oBugReport = cBugReport.foCreate(oCdbWrapper, sBugTypeId, sBugDescription, sSecurityImpact);
  if oCdbWrapper.bGenerateReportHTML:
    oBugReport.atxMemoryDumps.append(("Memory near heap block at 0x%X" % uMemoryDumpStartAddress, \
        uMemoryDumpStartAddress, uMemoryDumpSize));
    oBugReport.atxMemoryRemarks.extend(atxMemoryRemarks);
  # Output the VERIFIER STOP message for reference
  if oCdbWrapper.bGenerateReportHTML:
    sVerifierStopMessageHTML = sBlockHTMLTemplate % {
      "sName": "VERIFIER STOP message",
      "sCollapsed": "Collapsed",
      "sContent": "<pre>%s</pre>" % "\r\n".join([
        oCdbWrapper.fsHTMLEncode(s, uTabStop = 8) for s in asRelevantLines
      ])
    };
    oBugReport.asExceptionSpecificBlocksHTML.append(sVerifierStopMessageHTML);
    # Output the page heap information for reference
    if oPageHeapReport:
      sPageHeapOutputHTML = sBlockHTMLTemplate % {
        "sName": "Page heap output for heap block at 0x%X" % uHeapBlockStartAddress,
        "sCollapsed": "Collapsed",
        "sContent": "<pre>%s</pre>" % "\r\n".join([
          oCdbWrapper.fsHTMLEncode(s, uTabStop = 8) for s in oPageHeapReport.asPageHeapOutput
        ])
      };
      oBugReport.asExceptionSpecificBlocksHTML.append(sPageHeapOutputHTML);
  
  oBugReport.bRegistersRelevant = False;
  oCdbWrapper.oBugReport = oBugReport;
  return True;
