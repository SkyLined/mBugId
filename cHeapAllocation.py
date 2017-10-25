import re;
from cVirtualAllocation import cVirtualAllocation;
from cHeapAllocation_ftsGetIdAndDescriptionForAddress import cHeapAllocation_ftsGetIdAndDescriptionForAddress;

class cHeapAllocation(object):
  @staticmethod
  def foGetForProcessAndAddress(oProcess, uAddress):
    return cHeapAllocation.foGetForProcessAddressAndSize(oProcess, uAddress, None);
  @staticmethod
  def foGetForProcessAddressAndSize(oProcess, uAddress, uSize):
    # uSize is only used if page heap is enabled but it does not report the address and size of the heap block. In this
    # case uAddress is assumed to point to the start of the heap block and uSize is assumed to be its size.
    uPointerSize = oProcess.uPointerSize;
    asCdbHeapOutput = oProcess.fasExecuteCdbCommand(
      sCommand = "!heap -p -a 0x%X;" % uAddress,
      sComment = "Get page heap information",
      bOutputIsInformative = True,
    );
    # Sample output:
    # Allocated memory on "normal" hreap
    # |    address 000001ec4e8cc790 found in
    # |    _HEAP @ 1ec4e8c0000
    # |              HEAP_ENTRY Size Prev Flags            UserPtr UserSize - state
    # |        000001ec4e8cc740 0008 0000  [00]   000001ec4e8cc790    00010 - (busy)
    # |        7fff11ce401f verifier!AVrfDebugPageHeapAllocate+0x000000000000039f
    # |        7fff1bf6fd99 ntdll!RtlDebugAllocateHeap+0x000000000003bf65
    # |        7fff1bf5db7c ntdll!RtlpAllocateHeap+0x0000000000083fbc
    # |        7fff1bed8097 ntdll!RtlpAllocateHeapInternal+0x0000000000000727
    # ...
    
    # Delayed freed in "normal" heap:
    # |    address 000002572ef108f0 found in
    # |    _HEAP @ 2577f5f0000
    # |              HEAP_ENTRY Size Prev Flags            UserPtr UserSize - state
    # |        000002572ef108a0 0008 0000  [00]   000002572ef108f0    00010 - (free DelayedFree)
    # |        7ff9c4b5412f verifier!AVrfDebugPageHeapFree+0x00000000000000af
    # ...

    # Allocated memory on debug page heap
    # |    address 07fd1000 found in
    # |    _DPH_HEAP_ROOT @ 4fd1000
    # |    in busy allocation (  DPH_HEAP_BLOCK:         UserAddr         UserSize -         VirtAddr         VirtSize)
    # |                                 7f51d9c:          7fd0fc0               40 -          7fd0000             2000
    # |    6c469abc verifier!AVrfDebugPageHeapAllocate+0x0000023c
    # |...
    
    # Freed memory in debug page heap:
    # |    address 0e948ffc found in
    # |    _DPH_HEAP_ROOT @ 48b1000
    # |    in free-ed allocation (  DPH_HEAP_BLOCK:         VirtAddr         VirtSize)
    # |                                    e9f08bc:          e948000             2000
    # |    6d009cd2 verifier!AVrfDebugPageHeapFree+0x000000c2
    # |    77d42e20 ntdll!RtlDebugFreeHeap+0x0000003c
    # |    77cfe0da ntdll!RtlpFreeHeap+0x0006c97a
    # |    77cf5d2c ntdll!RtlpFreeHeapInternal+0x0000027e
    # |    77c90a3c ntdll!RtlFreeHeap+0x0000002c
    # |...
    
    
    # Errors:
    # |ReadMemory error for address 5b59c3d0
    # |Use `!address 5b59c3d0' to check validity of the address.
    # ----------------------------------------------------
    # |*************************************************************************
    # |***                                                                   ***
    # |***                                                                   ***
    # |***    Either you specified an unqualified symbol, or your debugger   ***
    # |***    doesn't have full symbol information.  Unqualified symbol      ***
    # |***    resolution is turned off by default. Please either specify a   ***
    # |***    fully qualified symbol module!symbolname, or enable resolution ***
    # |<<<snip>>>
    # |unable to resolve ntdll!RtlpStackTraceDataBase
    
    # Strip warnings and errors that we may be able to ignore:
    asCdbHeapOutput = [
      x for x in asCdbHeapOutput
      if not re.match(r"^(%s)\s*$" % "|".join([
        "ReadMemory error for address [0-9`a-f]+",
        "Use `!address [0-9`a-f]+' to check validity of the address.",
        "\*\*\*.*\*\*\*",
        "unable to resolve ntdll!RtlpStackTraceDataBase",
      ]), x)
    ];
    if len(asCdbHeapOutput) < 4:
      # No page heap output; make sure it is enabled for this process.
      oProcess.fEnsurePageHeapIsEnabled();
      return;
    # TODO: error resolving symbol should be handled by attempting to reload them, similar to cCdbWrapper_fasGetStack
    if asCdbHeapOutput[0].startswith("unable to resolve ntdll!"):
      return None;
    assert re.match(r"^\s+address [0-9`a-f]+ found in\s*$", asCdbHeapOutput[0]), \
        "Unrecognized page heap report first line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
    oHeapTypeMatch = re.match(r"^\s+(_HEAP|_DPH_HEAP_ROOT) @ [0-9`a-f]+\s*$", asCdbHeapOutput[1]);
    assert oHeapTypeMatch, \
        "Unrecognized page heap report second line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
    bPageHeap = oHeapTypeMatch.group(1) == "_DPH_HEAP_ROOT";
    if not bPageHeap:
      assert re.match( # line #3
        "^\s+%s\s*$" % "\s+".join([               # starts with spaces, separated by spaces and optionally end with spaces too
          r"HEAP_ENTRY", r"Size", r"Prev", r"Flags", r"UserPtr", r"UserSize", r"\-", r"state",
        ]),
        asCdbHeapOutput[2],
      ), \
          "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
      oBlockInformationMatch = re.match( # line #4 
        "^\s+%s\s*$" % "\s+".join([               # starts with spaces, separated by spaces and optionally end with spaces too
          r"([0-9`a-f]+)",                          # (heap_entry_address)
          r"([0-9`a-f]+)",                          # (heap_entry_size)
          r"[0-9`a-f]+",                            # prev
          r"\[" r"[0-9`a-f]+" r"\]",                # "[" flags "]"
          r"([0-9`a-f]+)",                          # (sBlockStartAddress)
          r"([0-9`a-f]+)",                          # (sBlockSize)
          r"\-",                                    # "-"
          r"\(" r"(busy|free DelayedFree)" r"\)",   # "(" (sState)  ")"
        ]),
        asCdbHeapOutput[3],
      );
      assert oBlockInformationMatch, \
          "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
      (
        sHeapManagerBlockStartAddress,
        sHeapManagerHeaderSizeInPointers,
        sBlockStartAddress,
        sBlockSize,
        sState,
      ) = oBlockInformationMatch.groups();
      uHeapManagerBlockDataStartAddress = long(sHeapManagerBlockStartAddress.replace("`", ""), 16);
      uHeapManagerBlockDataSize = long(sHeapManagerHeaderSizeInPointers.replace("`", ""), 16) * uPointerSize;
      uBlockStartAddress = long(sBlockStartAddress.replace("`", ""), 16);
      uBlockSize = long(sBlockSize.replace("`", ""), 16);
      if uSize:
        assert uBlockStartAddress == uAddress and uBlockSize == uSize, \
            "The heap block was expected to be 0x%X bytes @ 0x%X, but reported to be 0x%X bytes @ 0x%X" % \
            (uAddress, uSize, uBlockStartAddress, uBlockSize);
      bAllocated = sState == "busy";
      oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uBlockStartAddress);
    else:
      oDPHHeapBlockTypeMatch = re.match( # line #3
        "^\s+%s\s*$" % "\s+".join([                 # starts with spaces, separated by spaces and optionally end with spaces too
          r"in",                                        # "in"
          r"(free-ed|busy)",                            # (sState)
          r"allocation",                                # "allocation"
          r"\(" r"\s*" r"DPH_HEAP_BLOCK" r":",          # "(" [space] DPH_HEAP_BLOCK ":"
          r"(?:UserAddr",                               # optional{ "UserAddr" 
            r"UserSize",                                #           "UserSize"
            r"\-", ")?"                                 #           "-" }
          r"VirtAddr",                                  # "VirtAddr"
          r"VirtSize" r"\)",                            # "VirtSize" ")"
        ]),
        asCdbHeapOutput[2],
      );
      assert oDPHHeapBlockTypeMatch, \
          "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
      bAllocated = oDPHHeapBlockTypeMatch.group(1) == "busy";
      oBlockInformationMatch = re.match( # line #4
        "^\s+%s\s*$" % "\s+".join([                 # starts with spaces, separated by spaces and optionally end with spaces too
          r"[0-9`a-f]+" r":",                           # heap_header_address ":"
          r"(?:([0-9`a-f]+)",                           # optional{ (sBlockStartAddress)
            r"([0-9`a-f]+)",                            #           (sBlockSize)
            r"\-", r")?"                                #            "-" }
          r"([0-9`a-f]+)",                              # (sAllocationStartAddress)
          r"[0-9`a-f]+",                                # sAllocationSize
        ]),
        asCdbHeapOutput[3],
      );
      assert oBlockInformationMatch, \
          "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
      (
        sBlockStartAddress,
        sBlockSize,
        sAllocationStartAddress,
      ) = oBlockInformationMatch.groups();
      if sBlockStartAddress:
        uBlockStartAddress = long(sBlockStartAddress.replace("`", ""), 16);
        uBlockSize = long(sBlockSize.replace("`", ""), 16);
      elif uSize:
        # Information about the start address and size of the heap block appears to have been discarded by page heap,
        # but we still know this somehow, as it was provided through the arguments.
        uBlockStartAddress = uAddress;
        uBlockSize = uSize;
      else:
        # We have no information about the start address and size of the heap block related to the given address.
        uBlockStartAddress = None;
        uBlockSize = None;
      uAllocationStartAddress = long(sAllocationStartAddress.replace("`", ""), 16);
      oVirtualAllocation = oProcess.foGetVirtualAllocationForAddress(uAllocationStartAddress);
      # Find the heap manager (page heap) data that's stored before the heap block, if available.
      uHeapManagerBlockDataSize = sum([
        uPointerSize,      # ULONG StartStamp (with optional padding to pointer size)
        uPointerSize,      # PVOID Heap
        uPointerSize,      # size_t RequestedSize
        uPointerSize,      # size_t ActualSize
        uPointerSize * 2,  # LIST_ENTRY FreeQueue
        uPointerSize,      # PVOID StackTrace
        uPointerSize,      # ULONG EndStamp (with optional padding to pointer size)
       ]);
      if uBlockStartAddress:
        # We can calculate the start of the page heap data from the block start address:
        uHeapManagerBlockDataStartAddress = uBlockStartAddress - uHeapManagerBlockDataSize;
      elif oVirtualAllocation.bAllocated:
        # sBlockStartAddress and sBlockSize are sometimes not report after a heap block has been freed, but page heap
        # may not have freed the virtual allocation but made it inaccessible. So, the block start address and size can be
        # extracted from the page heap data stored in the virtual allocation if we make it accessible again. This
        # information can be found because the virtual allocation starts with 4 pointer sized values with unknown
        # meaning, followed by pointer sized 0 values, followed by the page heap data and the heap block. We'll find the
        # page heap struct by scanning for the first non-zero value after the first 4 pointer sized values:
        uStartStampOffset = uPointerSize * 4;
        while uStartStampOffset < oVirtualAllocation.uSize:
          # The rest of the block should be 0 up until the start stamp.
          uStartStamp = oVirtualAllocation.fuGetValueAtOffset(uStartStampOffset, 4);
          if uStartStamp != 0:
            break;
          uStartStampOffset += uPointerSize;
        else:
          raise AssertionError("Entire virtual allocation contains 0 bytes; page heap struct cannot be found!?");
        # Check that the first non-null byte is the start of the start stamp.
        assert uStartStamp == 0xABCDBBBA, \
            "Bad start stamp at offset 0x%X: 0x%X (%s)" % (uStartStampOffset, uStartStamp, \
            " ".join(["%02X" % u for u in oVirtualAllocation.fauGetBytesAtOffset(uStartStampOffset, 4)]));
        # We found the start address of the page heap data:
        uHeapManagerBlockDataStartAddress = uAllocationStartAddress + uStartStampOffset;
        # We can calculate the start address of the heap block, which comes immediately after it:
        uBlockStartAddress = uHeapManagerBlockDataStartAddress + uHeapManagerBlockDataSize;
        # We can read the size of the heap block from the page heap data:
        uOffsetOfBlockSizeInVirtualAllocation = sum([
          uStartStampOffset,  # page heap data {
          uPointerSize,       #   ULONG StartStamp (with optional padding to pointer size)
          uPointerSize,       #   PVOID Heap
        ]);                   # =>size_t RequestedSize
        uBlockSize = oVirtualAllocation.fuGetValueAtOffset(uOffsetOfBlockSizeInVirtualAllocation, uPointerSize);
      else:
        # No information is available
        uHeapManagerBlockDataStartAddress = uHeapManagerBlockDataSize = None;

    return cHeapAllocation(
      oVirtualAllocation,
      asCdbHeapOutput,
      bPageHeap,
      bAllocated,
      uHeapManagerBlockDataStartAddress,
      uHeapManagerBlockDataSize,
      uBlockStartAddress,
      uBlockSize,
      uPointerSize,
    );
  
  def __init__(oHeapAllocation,
      oVirtualAllocation,
      asCdbHeapOutput,
      bPageHeap,
      bAllocated,
      uHeapManagerBlockDataStartAddress,
      uHeapManagerBlockDataSize,
      uBlockStartAddress,
      uBlockSize,
      uPointerSize,
    ):
    oHeapAllocation.oVirtualAllocation = oVirtualAllocation;
    oHeapAllocation.asCdbHeapOutput = asCdbHeapOutput;
    oHeapAllocation.bPageHeap = bPageHeap;
    oHeapAllocation.bAllocated = bAllocated;
    oHeapAllocation.bFreed = not bAllocated;
    oHeapAllocation.uHeapManagerBlockDataStartAddress = uHeapManagerBlockDataStartAddress;
    oHeapAllocation.uHeapManagerBlockDataSize = uHeapManagerBlockDataSize;
    oHeapAllocation.uBlockStartAddress = uBlockStartAddress;
    oHeapAllocation.uBlockSize = uBlockSize;
    oHeapAllocation.uBlockEndAddress = uBlockStartAddress and uBlockStartAddress + uBlockSize;
    oHeapAllocation.uPointerSize = uPointerSize;
  
  @property
  def uAllocationStartAddress(oHeapAllocation):
    return oHeapAllocation.oVirtualAllocation.uAllocationBaseAddress;
  @property
  def uAllocationEndAddress(oHeapAllocation):
    return oHeapAllocation.oVirtualAllocation.uEndAddress;
  @property
  def uAllocationSize(oHeapAllocation):
    return oHeapAllocation.oVirtualAllocation.uSize;
  
  @property
  def uPostBlockPaddingSize(oHeapAllocation):
    if oHeapAllocation.bPageHeap:
      if oHeapAllocation.uBlockEndAddress is None:
        return None;
      return oHeapAllocation.uAllocationEndAddress - oHeapAllocation.uBlockEndAddress;
    return 0;
  
  @property
  def uStartStampAddress(oHeapAllocation):
    # ULONG StartStamp (with optional padding to pointer size);
    if not oHeapAllocation.bPageHeap: return None;
    return oHeapAllocation.uHeapManagerBlockDataStartAddress;
  @property
  def uHeapAddressAddress(oHeapAllocation):
    # PVOID Heap
    if not oHeapAllocation.uStartStampAddress: return None;
    return oHeapAllocation.uStartStampAddress + oHeapAllocation.uPointerSize;
  @property
  def uRequestedSizeAddress(oHeapAllocation):
    # size_t RequestedSize
    if not oHeapAllocation.uHeapAddressAddress: return None;
    return oHeapAllocation.uHeapAddressAddress + oHeapAllocation.uPointerSize;
  @property
  def uActualSizeAddress(oHeapAllocation):
    # size_t ActualSize
    if not oHeapAllocation.uRequestedSizeAddress: return None;
    return oHeapAllocation.uRequestedSizeAddress + oHeapAllocation.uPointerSize;
  @property
  def uFreeQueueAddress(oHeapAllocation):
    # LIST_ENTRY FreeQueue
    if not oHeapAllocation.uActualSizeAddress: return None;
    return oHeapAllocation.uActualSizeAddress + oHeapAllocation.uPointerSize;
  @property
  def uFreeQueueBLinkAddress(oHeapAllocation):
    # LIST_ENTRY FreeQueue.BLink
    if not oHeapAllocation.uFreeQueueAddress: return None;
    return oHeapAllocation.uFreeQueueAddress;
  @property
  def uFreeQueueFLinkAddress(oHeapAllocation):
    # LIST_ENTRY FreeQueue.FLink
    if not oHeapAllocation.uFreeQueueAddress: return None;
    return oHeapAllocation.uFreeQueueAddress + oHeapAllocation.uPointerSize;
  @property
  def uStackTraceAddress(oHeapAllocation):
    # PVOID StackTrace
    if not oHeapAllocation.uFreeQueueAddress: return None;
    return oHeapAllocation.uFreeQueueAddress + oHeapAllocation.uPointerSize * 2; # LIST_ENTRY FreeQueue is two pointers in size
  @property
  def uEndStampAddress(oHeapAllocation):
    # ULONG EndStamp (with optional padding to pointer size)
    if not oHeapAllocation.uStackTraceAddress: return None;
    return oHeapAllocation.uStackTraceAddress + oHeapAllocation.uPointerSize;
  
  def fatxMemoryRemarks(oHeapAllocation):
    atxMemoryRemarks = [];
    if oHeapAllocation.bPageHeap or not oHeapAllocation.uBlockStartAddress:
      atxMemoryRemarks.extend([
        ("Allocation start", oHeapAllocation.uAllocationStartAddress, None),
        ("Allocation end", oHeapAllocation.uAllocationEndAddress, None),
      ]);
    if oHeapAllocation.uStartStampAddress:
      atxMemoryRemarks += [
        ("Page heap ULONG start_stamp", oHeapAllocation.uStartStampAddress, None),
        ("Page heap PVOID heap_address", oHeapAllocation.uHeapAddressAddress, None),
        ("Page heap size_t requested_size", oHeapAllocation.uRequestedSizeAddress, None),
        ("Page heap size_t actual_size", oHeapAllocation.uActualSizeAddress, None),
        ("Page heap LIST_ENTRY free_queue.BLink", oHeapAllocation.uFreeQueueFLinkAddress, None),
        ("Page heap LIST_ENTRY free_queue.FLink", oHeapAllocation.uFreeQueueBLinkAddress, None),
        ("Page heap PVOID stack_trace", oHeapAllocation.uStackTraceAddress, None),
        ("Page heap ULONG end_stamp", oHeapAllocation.uEndStampAddress, None),
      ];
      if oHeapAllocation.uPointerSize > 4:
        # start and end stamp are followed by padding:
        uStampPaddingSize = oHeapAllocation.uPointerSize - 4;
        atxMemoryRemarks += [
          ("Page heap BYTE[%d] start_stamp_padding" % uStampPaddingSize, oHeapAllocation.uStartStampAddress + 4, None),
          ("Page heap BYTE[%d] end_stamp_padding" % uStampPaddingSize, oHeapAllocation.uEndStampAddress, None),
        ];
    if oHeapAllocation.uBlockStartAddress:
      atxMemoryRemarks += [
        ("Heap block start", oHeapAllocation.uBlockStartAddress, None),
        ("Heap block end", oHeapAllocation.uBlockEndAddress, None),
      ];
    if oHeapAllocation.uPostBlockPaddingSize:
      atxMemoryRemarks += [
        ("Page heap BYTE[%d] post_block_padding", oHeapAllocation.uPostBlockPaddingSize, None),
      ];
    return atxMemoryRemarks;
  
  def fCheckForCorruption(oHeapAllocation, oCorruptionDetector):
    if oHeapAllocation.uBlockStartAddress:
      uStampPaddingSize = oHeapAllocation.uPointerSize - 4;
      # Check start stamp and optional padding after start stamp
      axStartStamp = [[0xBA, 0xBB], 0xBB, 0xCD, 0xAB] + [0 for x in xrange(uStampPaddingSize)];
      oCorruptionDetector.fbDetectCorruption(oHeapAllocation.uStartStampAddress, axStartStamp);
      # Check optional padding before end stamp and end stamp itself
      axEndStamp = [0 for x in xrange(uStampPaddingSize)] + [[0xBA, 0xBB], 0xBB, 0xBA, 0xDC];
      oCorruptionDetector.fbDetectCorruption(oHeapAllocation.uEndStampAddress, axEndStamp);
      # Check optional padding after block
      if oHeapAllocation.uPostBlockPaddingSize:
        axPostBlockPadding = [0xD0 for x in xrange(oHeapAllocation.uPostBlockPaddingSize)]
        oCorruptionDetector.fbDetectCorruption(oHeapAllocation.uBlockEndAddress, axPostBlockPadding);
  
  def ftsGetIdAndDescriptionForAddress(oHeapAllocation, uAddress):
    return cHeapAllocation_ftsGetIdAndDescriptionForAddress(oHeapAllocation, uAddress);