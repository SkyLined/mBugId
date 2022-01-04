import re;

from mWindowsAPI import *;

# local imports are at the end of this file to avoid import loops.

gbDebugOutput = False;

class cVerifierStopDetector(object):
  def __init__(oSelf, oCdbWrapper):
    # Hook application debug output events to detect VERIFIER STOP messages
    oCdbWrapper.fAddCallback("Application debug output", oSelf.__fCheckDebugOutputForVerifierStopMessage);

  def __fCheckDebugOutputForVerifierStopMessage(oSelf, oCdbWrapper, oProcess, asbDebugOutput):
    # TODO: oThread should be an argument to the event callback
    oWindowsAPIThread = oCdbWrapper.oCdbCurrentWindowsAPIThread;
    # Detect VERIFIER STOP messages, create a cBugReport and report them before stopping cdb.
    if len(asbDebugOutput) == 0:
      return;
    obVerifierStopHeaderMatch = re.match(rb"^VERIFIER STOP ([0-9A-F]+): pid 0x([0-9A-F]+): (.*?)\s*$", asbDebugOutput[0]);
    if not obVerifierStopHeaderMatch:
      return;
    (sbErrorNumber, sbProcessId, sbMessage) = obVerifierStopHeaderMatch.groups();
    uErrorNumber = fu0ValueFromCdbHexOutput(sbErrorNumber);
    uProcessId = fu0ValueFromCdbHexOutput(sbProcessId);
    assert oProcess.uId == uProcessId, \
        "VERIFIER STOP reported in process %d, but cdb is debugging process %d" % (oProcess.uId, uProcessId);
    
    u0VerifierStopHeapBlockAddress = None;
    u0VerifierStopHeapBlockSize = None;
    u0VerifierStopHeapBlockHandle = None; 
    u0VerifierStopHeapHandle = None; # This is what is being used, which may differ from the actual heap handle of the block
    u0CorruptedStamp = None;
    u0CorruptionAddress = None;
    
    for sbLine in asbDebugOutput[1:]:
      # Ignore exmpty lines
      if not sbLine:
        continue;
      # Look for the first VERIFIER STOP message and gather information
      if uErrorNumber is None:
        continue;
      # A VERIFIER STOP message has been detected, gather what information verifier provides:
      obInformationMatch = re.match(rb"^\t([0-9A-F]+) : (.*?)\s*$", sbLine);
      assert obInformationMatch, \
          "Unhandled VERIFIER STOP message line: %s\r\n%s" % \
          (repr(sbLine), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput));
      (sbValue, sbDescription) = obInformationMatch.groups();
      uValue = fu0ValueFromCdbHexOutput(sbValue);
      sbDescription = sbDescription.lower(); # Both "Corruption address" and "corruption address" are used :(
      if sbDescription == b"heap block":
        u0VerifierStopHeapBlockAddress = uValue;
      elif sbDescription == b"block size":
        u0VerifierStopHeapBlockSize = uValue;
      elif sbDescription == b"corrupted stamp":
        u0CorruptedStamp = uValue;
      elif sbDescription == b"corruption address":
        u0CorruptionAddress = uValue;
      elif sbDescription == b"heap handle":
        u0VerifierStopHeapBlockHandle = uValue;
        u0VerifierStopHeapHandle = uValue;
      elif sbDescription == b"heap used in the call":
        u0VerifierStopHeapHandle = uValue;
      elif sbDescription == b"heap owning the block":
        u0VerifierStopHeapBlockHandle = uValue;
      else:
        # There are always exactly four values, not all of which are used to store information. Those that are not have
        # an empty or "Not used." description to indicates this.
        assert sbDescription in [b"", b"Not used."] and uValue == 0, \
            "Unhandled VERIFIER STOP message line: %s\r\n%s" % \
            (repr(sbLine), "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput));
    if uErrorNumber == 0x303:
      # |VERIFIER STOP 0000000000000303: pid 0xB2C: NULL handle passed as parameter. A valid handle must be used.
      # |
      # |0000000000000000 : Not used.
      # |0000000000000000 : Not used.
      # |0000000000000000 : Not used.
      # |0000000000000000 : Not used.
      # |
      return; # This is a VERIFIER STOP, but not an interesting one and we can continue the application.
    
    if gbDebugOutput:
      def fsValues(sFormat, u0Value1, u0Value2):
        if u0Value1 is None and u0Value2 is None:
          return "-";
        return sFormat % (
          ("0x%X" % u0Value1) if u0Value1 is not None else "-",
          ("0x%X" % u0Value2) if u0Value2 is not None else "-",
        );
      print("VERIFIER STOP debug output detected (heap block %s, handle %s, corruption %s)" % (
        fsValues("[%s]@%s", u0VerifierStopHeapBlockSize,  u0VerifierStopHeapBlockAddress),
        fsValues("%s/%s", u0VerifierStopHeapBlockHandle, u0VerifierStopHeapHandle),
        fsValues("%s@%s", u0CorruptedStamp, u0CorruptionAddress),
      ));
    
    assert u0VerifierStopHeapBlockAddress is not None, \
        "The heap block start address was not found in the verifier stop message.\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput);
    assert u0VerifierStopHeapBlockSize is not None, \
        "The heap block size was not found in the verifier stop message.\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput);
    
    o0PageHeapManagerData = oProcess.fo0GetHeapManagerDataForAddress(
      uAddress = u0VerifierStopHeapBlockAddress,
      s0ExpectedType = "page heap",
      bMayNotBeParseable = b"corrupted" in sbMessage,
    );
    if o0PageHeapManagerData is None and sbMessage == b"block already freed":
      if gbDebugOutput: print("VERIFIER STOP: freed block bug work around needed");
      # There is a bug in application verifier where it reports the address of the DPH_HEAP_BLOCK structure instead of
      # the heap block in certain situations. In this case, "!heap" will not return any information and
      # oPageHeapManagerData will be None. We can still find the correct information though:
      o0PageHeapManagerData = cPageHeapManagerData.fo0GetForProcessAndAllocationInformationStartAddress(
        oProcess,
        u0VerifierStopHeapBlockAddress,
      );
      if o0PageHeapManagerData:
        # Adjust the address accordingly.
        u0VerifierStopHeapBlockAddress = o0PageHeapManagerData.uHeapBlockStartAddress;
    
    uMemoryDumpStartAddress = None;
    atxMemoryRemarks = [];
    if o0PageHeapManagerData:
      if gbDebugOutput: print("VERIFIER STOP: page heap manager data found.", {
        "uHeapBlockStartAddress": o0PageHeapManagerData.uHeapBlockStartAddress,
        "uHeapBlockSize": o0PageHeapManagerData.uHeapBlockSize,
      });
      (sBlockSizeId, sBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = \
          o0PageHeapManagerData.ftsGetIdAndDescriptionForAddress(u0VerifierStopHeapBlockAddress);
    else:
      if gbDebugOutput: print("VERIFIER STOP: unable to get page heap manager data.");
      sBlockSizeId = "[%s]" % (fsGetNumberDescription(u0VerifierStopHeapBlockSize),);
      sBlockOffsetId = "@?";
      sBlockOffsetDescription = "at address 0x%08X in" % (u0VerifierStopHeapBlockAddress,);
      sBlockSizeDescription = "a heap block of %s" % (fsNumberOfBytes(u0VerifierStopHeapBlockSize),);
    sBlockSizeAndOffsetId = sBlockSizeId + sBlockOffsetId;
    sBlockOffsetAndSizeDescription = sBlockOffsetDescription + " " + sBlockSizeDescription;
    if (
      sbMessage == b"corrupted start stamp" \
      and u0CorruptedStamp == 0xABCDBBBA \
      and o0PageHeapManagerData
      and not o0PageHeapManagerData.oVirtualAllocation.bReserved
    ):
      if gbDebugOutput: print("VERIFIER STOP: corrupted start stamp reported but not confirmed.");
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
      sbMessage in [b"corrupted start stamp", b"corrupted end stamp"]
      and o0PageHeapManagerData
      and o0PageHeapManagerData.uHeapBlockStartAddress != u0VerifierStopHeapBlockAddress
    ):
      if gbDebugOutput: print("VERIFIER STOP: corrupted stamp reported indicates a misalligned free.");
      # When the application attempts to free (heap pointer + offset), Verifier does not detect this and will assume
      # the application provided pointer is correct. This causes it to look for the start and end stamp in the wrong
      # location and report this bug as memory corruption. When the page heap data shows no signs of corruption, we
      # can special case it.
      sBugTypeId = "MisalignedFree%s" % sBlockSizeAndOffsetId;
      sBugDescription = "The application attempted to free memory using a pointer that was %s." % \
          sBlockOffsetAndSizeDescription;
      sSecurityImpact = "Unknown: this type of bug has not been analyzed before";
    elif sbMessage == b"block already freed":
      if gbDebugOutput: print("VERIFIER STOP: double free reported.");
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
    elif sbMessage == b"corrupted heap pointer or using wrong heap":
      if gbDebugOutput: print("VERIFIER STOP: wrong heap handle reported.");
      # |VERIFIER STOP 00000006: pid 0x144C: corrupted heap pointer or using wrong heap 
      # |
      # |        077F1000 : Heap used in the call
      # |        43742FE0 : Heap block
      # |        00000020 : Block size
      # |        277F1000 : Heap owning the block
      assert u0VerifierStopHeapHandle is not None, \
          "Missing 'Heap used in the call' value in the VERIFIER STOP message.\r\n%s" % \
          "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput);
      assert u0VerifierStopHeapBlockHandle is not None, \
          "Missing 'Heap owning the block' value in the VERIFIER STOP message.\r\n%s" % \
          "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput);
      sBugTypeId = "WrongHeap%s" % sBlockSizeId;
      sBugDescription = "The application provided an incorrect heap handle (0x%X) for %s which belongs to another " \
          "heap (handle 0x%X)" % (u0VerifierStopHeapHandle, sBlockSizeDescription, u0VerifierStopHeapBlockHandle);
      sSecurityImpact = "Unknown: this type of bug has not been analyzed before";
    else:
      if oCdbWrapper.bGenerateReportHTML and o0PageHeapManagerData:
        # Theoretically we could use the virtual allocation data in page heap manager data is missing, but that's a lot
        # of work for a situation that should happen very little.
        uMemoryDumpStartAddress = o0PageHeapManagerData.uMemoryDumpStartAddress;
        uMemoryDumpEndAddress = o0PageHeapManagerData.uMemoryDumpEndAddress;
        atxMemoryRemarks.extend(o0PageHeapManagerData.fatxMemoryRemarks());
        
      # Handle various VERIFIER STOP messages.
      if sbMessage in [b"corrupted start stamp", b"corrupted end stamp"]:
        assert u0CorruptionAddress is None, \
            "We do not expect the corruption address to be provided in this VERIFIER STOP message\r\n%s" % \
            "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput);
        if not o0PageHeapManagerData or not o0PageHeapManagerData.o0HeapBlockHeader:
          if gbDebugOutput: print("VERIFIER STOP: corrupted stamp reported but block is already free!?");
          # This makes no sense: there is no heap block header because the memory is really freed by verifier but left
          # reserved to prevent it from being reallocated. So the start and end stamp no longer exist...
          assert not o0PageHeapManagerData or o0PageHeapManagerData.oVirtualAllocation.bReserved, \
              "This is even more unexpected.";
          sBugAccessTypeId = "UnknownVerifierError";
          uExpectedCorruptionStartAddress = None;
          uExpectedCorruptionEndAddress = None;
        else:
          oPageHeapManagerData = o0PageHeapManagerData;
          sBugAccessTypeId = "OOBW";
          if sbMessage == b"corrupted start stamp":
            if gbDebugOutput: print("VERIFIER STOP: corrupted start stamp reported.");
            uExpectedCorruptionStartAddress = oPageHeapManagerData.fuHeapBlockHeaderFieldAddress("StartStamp");
            uExpectedCorruptionEndAddress = uExpectedCorruptionStartAddress + \
                oPageHeapManagerData.fuHeapBlockHeaderFieldSize("StartStamp");
          else:
            if gbDebugOutput: print("VERIFIER STOP: corrupted end stamp reported.");
            uExpectedCorruptionStartAddress = oPageHeapManagerData.fuHeapBlockHeaderFieldAddress("EndStamp");
            uExpectedCorruptionEndAddress = uExpectedCorruptionStartAddress + \
                oPageHeapManagerData.fuHeapBlockHeaderFieldSize("EndStamp");
      elif sbMessage in [b"corrupted suffix pattern", b"corrupted header"]:
        if gbDebugOutput: print("VERIFIER STOP: corrupted stamp/header reported, indicating an out-of-bounds write.");
        assert u0CorruptionAddress is not None, \
            "The corruption address is expected to be provided in this VERIFIER STOP message:\r\n%s" % \
            "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput);
        # Page heap stores the heap as close as possible to the edge of a page, taking into account that the start of the
        # heap block must be properly aligned. Bytes between the heap block and the end of the page are initialized to
        # 0xD0. Verifier has detected that one of the bytes changed value, which indicates an out-of-bounds write. BugId
        # will try to find all bytes that were changed:
        sBugAccessTypeId = "OOBW";
        uExpectedCorruptionStartAddress = u0CorruptionAddress;
        uExpectedCorruptionEndAddress = u0CorruptionAddress + 1; # We do not know the size, so assume one byte.
      elif sbMessage == b"corrupted infix pattern":
        if gbDebugOutput: print("VERIFIER STOP: corrupted infix reported, indicating an out-of-bounds write.");
        assert u0CorruptionAddress is not None, \
            "The corruption address is expected to be provided in the VERIFIER STOP message:\r\n%s" % \
            "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbDebugOutput);
        # Page heap sometimes does not free a heap block immediately, but overwrites the bytes with 0xF0. Verifier has
        # detected that one of the bytes changed value, which indicates a write-after-free. BugId will try to find all
        # bytes that were changed:
        uExpectedCorruptionStartAddress = u0CorruptionAddress;
        uExpectedCorruptionEndAddress = u0CorruptionAddress + 1; # We do not know the size, so assume one byte.
        sBugAccessTypeId = "WAF";
      else:
        if gbDebugOutput: print("VERIFIER STOP: unknown error message %s." % fsCP437FromBytesString(sbMessage));
        raise AssertionError("Unhandled VERIFIER STOP message: %s" % fsCP437FromBytesString(sbMessage));
      # We cannot trust the information in the VERIFIER STOP message: if you run the test "OutOfBounds Heap Write 1 -1 1"
      # (meaning you allocate 1 byte, write 1 byte at offset -1) you would expect it to report that the "end stamp" of
      # the heap block header was corrupted. HOWEVER IT INCORRECTLY REPORTS THAT THE START STAMP WAS CORRUPTED. So, only
      # if we cannot detect any corruption ourselves will we use the information we got from the VERIFIER STOP message.
      if not o0PageHeapManagerData or not o0PageHeapManagerData.bCorruptionDetected:
        if gbDebugOutput: print("VERIFIER STOP: reported corruption was not detected!?");
        sBugDescription = "Heap corruption reported but not detected %s." % sBlockOffsetAndSizeDescription;
        sSecurityImpact = "Unknown - Application Verifier reported this but it could not be confirmed.";
        sCorruptionId = "{?}";
      else:
        oPageHeapManagerData = o0PageHeapManagerData;
        uExpectedCorruptionStartAddress = oPageHeapManagerData.uCorruptionStartAddress;
        uExpectedCorruptionEndAddress = oPageHeapManagerData.uCorruptionEndAddress;
        sCorruptionId = "{%s}" % oPageHeapManagerData.sCorruptionId;
        (sIgnoredBlockSizeId, sIgnoredBlockOffsetId, sBlockOffsetDescription, sBlockSizeDescription) = oPageHeapManagerData.ftsGetIdAndDescriptionForAddress( \
            oPageHeapManagerData.uCorruptionStartAddress);
        sBugDescription = "Heap corruption detected at 0x%X; %s %s." % \
            (oPageHeapManagerData.uCorruptionStartAddress, sBlockOffsetDescription, sBlockSizeDescription);
        if oPageHeapManagerData.uCorruptionStartAddress == oPageHeapManagerData.uHeapBlockEndAddress:
          if gbDebugOutput: print("VERIFIER STOP: reported corruption at end of block indicates classic buffer-overrun");
          sBugAccessTypeId = "BOF";
          sBugDescription += " This appears to be a classic buffer-overrun vulnerability.";
          sSecurityImpact = "Potentially highly exploitable security issue.";
        else:
          sSecurityImpact = "Potentially exploitable security issue, if the corruption is attacker controlled.";
      sBugTypeId = sBugAccessTypeId +  sBlockSizeId + sCorruptionId;
      if uExpectedCorruptionStartAddress and oCdbWrapper.bGenerateReportHTML:
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
    
    oBugReport = cBugReport.foCreate(oCdbWrapper, oProcess, oWindowsAPIThread, sBugTypeId, sBugDescription, sSecurityImpact);
    if oCdbWrapper.bGenerateReportHTML:
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
          fsCP437HTMLFromBytesString(sbLine, u0TabStop = 8) for sbLine in asbDebugOutput
        ])
      };
      oBugReport.asExceptionSpecificBlocksHTML.append(sVerifierStopMessageHTML);
    
    oBugReport.bRegistersRelevant = False;
    oBugReport.fReport();
    oCdbWrapper.fStop();

from .cBugReport import cBugReport;
from .cPageHeapManagerData import cPageHeapManagerData;
from .dxConfig import dxConfig;
from .fsGetNumberDescription import fsGetNumberDescription;
from .fsNumberOfBytes import fsNumberOfBytes;
from .ftuLimitedAndAlignedMemoryDumpStartAddressAndSize import ftuLimitedAndAlignedMemoryDumpStartAddressAndSize;
from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .mCP437 import fsCP437FromBytesString, fsCP437HTMLFromBytesString;
