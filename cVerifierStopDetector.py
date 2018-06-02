import re;
from .cBugReport import cBugReport;
from .cPageHeapManagerData import cPageHeapManagerData;
from .dxConfig import dxConfig;
from .fsGetNumberDescription import fsGetNumberDescription;
from .ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from mWindowsAPI import *;

class cVerifierStopDetector(object):
  def __init__(oSelf, oCdbWrapper):
    # Hook application debug output events to detect VERIFIER STOP messages
    oSelf.oCdbWrapper = oCdbWrapper;
    oCdbWrapper.fAddEventCallback("Application debug output", oSelf.__fCheckDebugOutputForVerifierStopMessage);

  def __fCheckDebugOutputForVerifierStopMessage(oSelf, oProcess, asDebugOutput):
    # TODO: oThread should be an argument to the event callback
    oThread = oProcess.oCdbWrapper.oCdbCurrentThread;
    # Detect VERIFIER STOP messages, create a cBugReport and report them before stopping cdb.
    if len(asDebugOutput) == 0:
      return;
    oVerifierStopHeaderMatch = re.match(r"^VERIFIER STOP ([0-9A-F]+): pid 0x([0-9A-F]+): (.*?)\s*$", asDebugOutput[0]);
    if not oVerifierStopHeaderMatch:
      return;
    sErrorNumber, sProcessId, sMessage = oVerifierStopHeaderMatch.groups();
    uErrorNumber = long(sErrorNumber, 16);
    uProcessId = long(sProcessId, 16);
    assert oProcess.uId == uProcessId, \
        "VERIFIER STOP reported in process %d, but cdb is debugging process %d" % (oProcess.uId, uProcessId);
    
    uVerifierStopHeapBlockAddress = None;
    uVerifierStopHeapBlockSize = None;
    uVerifierStopHeapBlockHandle = None; 
    uVerifierStopHeapHandle = None; # This is what is being used, which may differ from the actual heap handle of the block
    uCorruptedStamp = None;
    uCorruptionAddress = None;
    
    for sLine in asDebugOutput[1:]:
      # Ignore exmpty lines
      if not sLine:
        continue;
      # Look for the first VERIFIER STOP message and gather information
      if uErrorNumber is None:
        continue;
      # A VERIFIER STOP message has been detected, gather what information verifier provides:
      oInformationMatch = re.match(r"^\t([0-9A-F]+) : (.*?)\s*$", sLine);
      assert oInformationMatch, \
          "Unhandled VERIFIER STOP message line: %s\r\n%s" % (repr(sLine), "\r\n".join(asDebugOutput));
      sValue, sDescription = oInformationMatch.groups();
      uValue = long(sValue, 16);
      sDescription = sDescription.lower(); # Both "Corruption address" and "corruption address" are used :(
      if sDescription == "heap block":
        uVerifierStopHeapBlockAddress = uValue;
      elif sDescription == "block size":
        uVerifierStopHeapBlockSize = uValue;
      elif sDescription == "corrupted stamp":
        uCorruptedStamp = uValue;
      elif sDescription == "corruption address":
        uCorruptionAddress = uValue;
      elif sDescription == "corruption address":
        uCorruptionAddress = uValue;
      elif sDescription == "heap handle":
        uVerifierStopHeapBlockHandle = uValue;
        uVerifierStopHeapHandle = uValue;
      elif sDescription == "heap used in the call":
        uVerifierStopHeapHandle = uValue;
      elif sDescription == "heap owning the block":
        uVerifierStopHeapBlockHandle = uValue;
      else:
        # There are always exactly four values, not all of which are used to store information. Those that are not have
        # an empty or "Not used." description to indicates this.
        assert sDescription in ["", "Not used."] and uValue == 0, \
            "Unhandled VERIFIER STOP message line: %s\r\n%s" % (repr(sLine), "\r\n".join(asDebugOutput));
    if uErrorNumber == 0x303:
      # |VERIFIER STOP 0000000000000303: pid 0xB2C: NULL handle passed as parameter. A valid handle must be used.
      # |
      # |0000000000000000 : Not used.
      # |0000000000000000 : Not used.
      # |0000000000000000 : Not used.
      # |0000000000000000 : Not used.
      # |
      return; # This is a VERIFIER STOP, but not an interesting one and we can continue the application.
    
    assert uVerifierStopHeapBlockAddress is not None, \
        "The heap block start address was not found in the verifier stop message.\r\n%s" % "\r\n".join(asDebugOutput);
    assert uVerifierStopHeapBlockSize is not None, \
        "The heap block size was not found in the verifier stop message.\r\n%s" % "\r\n".join(asDebugOutput);
    
    oPageHeapManagerData = oProcess.foGetHeapManagerDataForAddress(uVerifierStopHeapBlockAddress, sType = "page heap");
    if oPageHeapManagerData is None and sMessage == "block already freed":
      # There is a bug in application verifier where it reports the address of the DPH_HEAP_BLOCK structure instead of
      # the heap block in certain situations. In this case, "!heap" will not return any information and
      # oPageHeapManagerData will be None. We can still find the correct information though:
      oPageHeapManagerData = cPageHeapManagerData.foGetForProcessAndAllocationInformationStartAddress(
        oProcess,
        uVerifierStopHeapBlockAddress,
      );
      # Adjust the address accordingly.
      uVerifierStopHeapBlockAddress = oPageHeapManagerData.uHeapBlockStartAddress;
    
    uMemoryDumpStartAddress = None;
    atxMemoryRemarks = [];
    if oPageHeapManagerData:
      (sBlockSizeId, sBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = \
          oPageHeapManagerData.ftsGetIdAndDescriptionForAddress(uVerifierStopHeapBlockAddress);
      sBlockSizeAndOffsetId = sBlockSizeId + sBlockOffsetId;
      sBlockOffsetAndSizeDescription = sBlockOffsetDescription + " " + sBlockSizeDescription;
    else:
      sBlockSizeAndOffsetId = "[?]";
      sBlockOffsetAndSizeDescription = "at an unknown offset from a heap block of unknown size at an unknown address " \
          "somewhere around 0x%08X" % (uVerifierStopHeapBlockAddress);
    if (
      sMessage == "corrupted start stamp" \
      and uCorruptedStamp == 0xABCDBBBA \
      and oPageHeapManagerData
      and not oPageHeapManagerData.oVirtualAllocation.bReserved
    ):
      # Verifier sometimes reports this and I am not sure what is going on. Page heap will report that the heap block was
      # freed by the current function on the stack, while verifier reports this error almost immediately after that (from
      # that same stack). However, the start stamp reported in the verifier error is a valid value indicating the memory
      # was freed, so it makes no sense that it is reported as being corrupt. Also, there is no memory allocated at the
      # given address; it is only reserved, so it cannot actually contain a value.
      # I cannot think of any situation in which all this information is correct, and I suspect that verifier is
      # reporting the wrong kind of error. However, I have been unable to find a reliable repro for this to debug, so I
      # do not know exactly what is going on and what to report...
      sBugTypeId = "UnknownVerifierError%s" % sBlockSizeAndOffsetId;
      sBugDescription = "Application verifier reported a corrupt memory block, but no memory is allocated at the " \
          "address provided. This suggests that the verfier report is incorrect. However, it is likely that the " \
          "application does have some kind of memory corruption bug that triggers this report, but it is unknown " \
          "what kind of bug that might be. If you can reliably reproduce this, please contact the author of BugId " \
          "so this situation can be analyzed and BugId can be improved to report something more helpful here.";
      sSecurityImpact = "Unknown: this type of bug has not been analyzed before";
    elif (
      sMessage in ["corrupted start stamp", "corrupted end stamp"]
      and oPageHeapManagerData
      and oPageHeapManagerData.uHeapBlockStartAddress != uVerifierStopHeapBlockAddress
    ):
      # When the application attempts to free (heap pointer + offset), Verifier does not detect this and will assume
      # the application provided pointer is correct. This causes it to look for the start and end stamp in the wrong
      # location and report this bug as memory corruption. When the page heap data shows no signs of corruption, we
      # can special case it.
      sBugTypeId = "MisalignedFree%s" % sBlockSizeAndOffsetId;
      sBugDescription = "The application attempted to free memory using a pointer that was %s." % \
          sBlockOffsetAndSizeDescription;
      sSecurityImpact = "Unknown: this type of bug has not been analyzed before";
    elif sMessage == "block already freed":
      # |VERIFIER STOP 00000007: pid 0x1358: block already freed
      # |
      # |        02F71000 : Heap handle
      # |        152F016C : Heap block
      # |        000004C8 : Block size
      # |        00000000 :
      sBugTypeId = "DoubleFree%s" % sBlockSizeId;
      sBugDescription = "The application attempted to free %s twice" % sBlockSizeDescription;
      sSecurityImpact = "Potentially exploitable security issue, if the attacker can force the application to " \
          "allocate memory between the two frees";
    elif sMessage == "corrupted heap pointer or using wrong heap":
      # |VERIFIER STOP 00000006: pid 0x144C: corrupted heap pointer or using wrong heap 
      # |
      # |        077F1000 : Heap used in the call
      # |        43742FE0 : Heap block
      # |        00000020 : Block size
      # |        277F1000 : Heap owning the block
      assert uVerifierStopHeapHandle is not None, \
          "Missing 'Heap used in the call' value in the VERIFIER STOP message.\r\n%s" % "\r\n".join(asDebugOutput);
      assert uVerifierStopHeapBlockHandle is not None, \
          "Missing 'Heap owning the block' value in the VERIFIER STOP message.\r\n%s" % "\r\n".join(asDebugOutput);
      sBugTypeId = "WrongHeap%s" % sBlockSizeId;
      sBugDescription = "The application provided an incorrect heap handle (0x%X) for %s which belongs to another " \
          "heap (handle 0x%X)" % (uVerifierStopHeapHandle, sBlockSizeDescription, uVerifierStopHeapBlockHandle);
      sSecurityImpact = "Unknown: this type of bug has not been analyzed before";
    else:
      if oSelf.oCdbWrapper.bGenerateReportHTML and oPageHeapManagerData:
        # Theoretically we could use the virtual allocation data in page heap manager data is missing, but that's a lot
        # of work for a situation that should happen very little.
        uMemoryDumpStartAddress = oPageHeapManagerData.uMemoryDumpStartAddress;
        uMemoryDumpEndAddress = oPageHeapManagerData.uMemoryDumpEndAddress;
        atxMemoryRemarks.extend(oPageHeapManagerData.fatxMemoryRemarks());
        
      # Handle various VERIFIER STOP messages.
      if sMessage in ["corrupted start stamp", "corrupted end stamp"]:
        assert uCorruptionAddress is None, \
            "We do not expect the corruption address to be provided in this VERIFIER STOP message\r\n%s" % \
                "\r\n".join(asDebugOutput);
        if not oPageHeapManagerData or not oPageHeapManagerData.oHeapBlockHeader:
          # This makes no sense: there is no heap block header because the memory is really freed by verifier but left
          # reserved to prevent it from being reallocated. So the start and end stamp no longer exist...
          assert oPageHeapManagerData.oVirtualAllocation.bReserved, \
              "This is even more unexpected.";
          sBugAccessTypeId = "UnknownVerifierError";
          uExpectedCorruptionStartAddress = None;
          uExpectedCorruptionEndAddress = None;
        else:
          sBugAccessTypeId = "OOBW";
          if sMessage == "corrupted start stamp":
            uExpectedCorruptionStartAddress = oPageHeapManagerData.fuHeapBlockHeaderFieldAddress("StartStamp");
            uExpectedCorruptionEndAddress = uExpectedCorruptionStartAddress + \
                oPageHeapManagerData.fuHeapBlockHeaderFieldSize("StartStamp");
          else:
            uExpectedCorruptionStartAddress = oPageHeapManagerData.fuHeapBlockHeaderFieldAddress("EndStamp");
            uExpectedCorruptionEndAddress = uExpectedCorruptionStartAddress + \
                oPageHeapManagerData.fuHeapBlockHeaderFieldSize("EndStamp");
      elif sMessage in ["corrupted suffix pattern", "corrupted header"]:
        assert uCorruptionAddress is not None, \
            "The corruption address is expected to be provided in this VERIFIER STOP message:\r\n%s" % \
                "\r\n".join(asDebugOutput);
        # Page heap stores the heap as close as possible to the edge of a page, taking into account that the start of the
        # heap block must be properly aligned. Bytes between the heap block and the end of the page are initialized to
        # 0xD0. Verifier has detected that one of the bytes changed value, which indicates an out-of-bounds write. BugId
        # will try to find all bytes that were changed:
        sBugAccessTypeId = "OOBW";
        uExpectedCorruptionStartAddress = uCorruptionAddress;
        uExpectedCorruptionEndAddress = uCorruptionAddress + 1; # We do not know the size, so assume one byte.
      elif sMessage == "corrupted infix pattern":
        assert uCorruptionAddress is not None, \
            "The corruption address is expected to be provided in the VERIFIER STOP message:\r\n%s" % \
                "\r\n".join(asDebugOutput);
        # Page heap sometimes does not free a heap block immediately, but overwrites the bytes with 0xF0. Verifier has
        # detected that one of the bytes changed value, which indicates a write-after-free. BugId will try to find all
        # bytes that were changed:
        uExpectedCorruptionStartAddress = uCorruptionAddress;
        uExpectedCorruptionEndAddress = uCorruptionAddress + 1; # We do not know the size, so assume one byte.
        sBugAccessTypeId = "WAF";
      else:
        raise AssertionError("Unhandled VERIFIER STOP message: %s" % sMessage);
      # We cannot trust the information in the VERIFIER STOP message: if you run the test "OutOfBounds Heap Write 1 -1 1"
      # (meaning you allocate 1 byte, write 1 byte at offset -1) you would expect it to report that the "end stamp" of
      # the heap block header was corrupted. HOWEVER IT INCORRECTLY REPORTS THAT THE START STAMP WAS CORRUPTED. So, only
      # if we cannot detect any corruption ourselves will we use the information we got from the VERIFIER STOP message.
      if not oPageHeapManagerData or not oPageHeapManagerData.bCorruptionDetected:
        sBugDescription = "Heap corruption reported but not detected %s." % sBlockOffsetAndSizeDescription;
        sSecurityImpact = "Unknown - Application Verifier reported this but it could not be confirmed.";
        sCorruptionId = "{?}";
      else:
        uExpectedCorruptionStartAddress = oPageHeapManagerData.uCorruptionStartAddress;
        uExpectedCorruptionEndAddress = oPageHeapManagerData.uCorruptionEndAddress;
        sCorruptionId = "{%s}" % oPageHeapManagerData.sCorruptionId;
        (sIgnoredBlockSizeId, sIgnoredBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = oPageHeapManagerData.ftsGetIdAndDescriptionForAddress( \
            oPageHeapManagerData.uCorruptionStartAddress);
        sBugDescription = "Heap corruption detected at 0x%X; %s %s." % \
            (oPageHeapManagerData.uCorruptionStartAddress, sBlockOffsetDescription, sBlockSizeDescription);
        if oPageHeapManagerData.uCorruptionStartAddress == oPageHeapManagerData.uHeapBlockEndAddress:
          sBugAccessTypeId = "BOF";
          sBugDescription += " This appears to be a classic buffer-overrun vulnerability.";
          sSecurityImpact = "Potentially highly exploitable security issue.";
        else:
          sSecurityImpact = "Potentially exploitable security issue, if the corruption is attacker controlled.";
      sBugTypeId = sBugAccessTypeId +  sBlockSizeId + sCorruptionId;
      if uExpectedCorruptionStartAddress and oSelf.oCdbWrapper.bGenerateReportHTML:
        # Expand memory dump size to include all corrupted memory if needed
        if uExpectedCorruptionStartAddress < uMemoryDumpStartAddress:
          uMemoryDumpStartAddress = uExpectedCorruptionStartAddress;
        if uExpectedCorruptionEndAddress > uMemoryDumpEndAddress:
          uMemoryDumpEndAddress = uExpectedCorruptionEndAddress;
        # Limit memory dump size if needed.
        uMemoryDumpStartAddress, uMemoryDumpSize = ftuLimitedAndAlignedMemoryDumpStartAddressAndSize(
          uExpectedCorruptionStartAddress,
          oProcess.uPointerSize,
          uMemoryDumpStartAddress,
          uMemoryDumpEndAddress - uMemoryDumpStartAddress
        );
    
    oBugReport = cBugReport.foCreate(oProcess, oThread, sBugTypeId, sBugDescription, sSecurityImpact);
    if oSelf.oCdbWrapper.bGenerateReportHTML:
      if uMemoryDumpStartAddress:
        oBugReport.fAddMemoryDump(
          uMemoryDumpStartAddress,
          uMemoryDumpStartAddress + uMemoryDumpSize,
          "Memory at 0x%X" % uMemoryDumpStartAddress,
        );
        oBugReport.atxMemoryRemarks.extend(atxMemoryRemarks);
      # Output the VERIFIER STOP message for reference
      sVerifierStopMessageHTML = sBlockHTMLTemplate % {
        "sName": "VERIFIER STOP message",
        "sCollapsed": "Collapsed",
        "sContent": "<pre>%s</pre>" % "\r\n".join([
          oSelf.oCdbWrapper.fsHTMLEncode(s, uTabStop = 8) for s in asDebugOutput
        ])
      };
      oBugReport.asExceptionSpecificBlocksHTML.append(sVerifierStopMessageHTML);
    
    oBugReport.bRegistersRelevant = False;
    oBugReport.fReport(oSelf.oCdbWrapper);
    oSelf.oCdbWrapper.fStop();