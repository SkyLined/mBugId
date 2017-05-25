import re;
from cCorruptionDetector import cCorruptionDetector;
from cVirtualAllocation import cVirtualAllocation;

class cPageHeapAllocation(object):
  @staticmethod
  def foGetForAddress(oCdbWrapper, uAddress):
    asPageHeapOutput = oCdbWrapper.fasSendCommandAndReadOutput(
      "!heap -p -a 0x%X; $$ Get page heap information" % uAddress,
      bOutputIsInformative = True,
    );
    # Sample output:
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
    asPageHeapOutput = [
      x for x in asPageHeapOutput
      if not re.match(r"^(%s)\s*$" % "|".join([
        "ReadMemory error for address [0-9`a-f]+",
        "Use `!address [0-9`a-f]+' to check validity of the address.",
        "\*\*\*.*\*\*\*",
        "unable to resolve ntdll!RtlpStackTraceDataBase",
      ]), x)
    ];
    # TODO: error resolving symbol should be handled by attempting to reload them, similar to cCdbWrapper_fasGetStack
    if len(asPageHeapOutput) < 4 or asPageHeapOutput[0].startswith("unable to resolve ntdll!"):
      return None;
    assert re.match(r"^\s+address [0-9`a-f]+ found in\s*$", asPageHeapOutput[0]), \
        "Unrecognized page heap report first line:\r\n%s" % "\r\n".join(asPageHeapOutput);
    oHeapTypeMatch = re.match(r"^\s+(_HEAP|_DPH_HEAP_ROOT) @ [0-9`a-f]+\s*$", asPageHeapOutput[1]);
    assert oHeapTypeMatch, \
        "Unrecognized page heap report second line:\r\n%s" % "\r\n".join(asPageHeapOutput);
    sHeapType = oHeapTypeMatch.group(1); # "_HEAP" or "_DPH_HEAP_ROOT"
    if sHeapType == "_HEAP":
      oHeapBlockTypeMatch = re.match(                   # line #3
        r"^\s+HEAP_ENTRY\s+Size\s+Prev\s+Flags\s+UserPtr\s+UserSize\s+\-\s+state",
        asPageHeapOutput[2],
      );
      assert oDPHHeapBlockTypeMatch or oHeapBlockTypeMatch, \
          "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asPageHeapOutput);
      oBlockInformationMatch = re.match(            # line #4
        r"^\s+[0-9`a-f]+"                             # space heap_entry_address
        r"^\s+[0-9`a-f]+"                             # space heap_entry_size
        r"^\s+[0-9`a-f]+"                             # space prev
        r"^\s+\[[0-9`a-f]+\]"                         # space "[" flags "]"
        r"^\s+([0-9`a-f]+)"                           # space (sBlockStartAddress)
        r"^\s+([0-9`a-f]+)"                           # space (sBlockSize)
        r"^\s+\-\s+\((busy|free DelayedFree)\)"       # space "-" space "(" busy ")"
        r"\s*$",                                      # [space]
        asPageHeapOutput[3],
      );
      assert oBlockInformationMatch, \
          "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asPageHeapOutput);
      sBlockStartAddress, sBlockSize, sState = oBlockInformationMatch.groups();
      bAllocated == sState == "busy";
      uAllocationStartAddress, uAllocationSize = None, None; # Not applicable
    else:
      oDPHHeapBlockTypeMatch = re.match(                # line #3
        r"^\s+in (free-ed|busy) allocation \("          # space "in" space ("free-ed" | "busy") space  "allocation ("
        r"\s*\w+:"                                      #   [space] DPH_HEAP_BLOCK ":"
        r"(?:\s+UserAddr\s+UserSize\s+\-)?"             #   optional{ space "UserAddr" space "UserSize" space "-" }
        r"\s+VirtAddr\s+VirtSize"                       #   space "VirtAddr" space "VirtSize"
        r"\)\s*$",                                      # ")" [space]
        asPageHeapOutput[2],
      );
      assert oDPHHeapBlockTypeMatch, \
          "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asPageHeapOutput);
      bAllocated = oDPHHeapBlockTypeMatch.group(1) == "busy";
      oBlockInformationMatch = re.match(            # line #4
        r"^\s+[0-9`a-f]+:"                            # space heap_header_address ":"
        r"(?:\s+([0-9`a-f]+)\s+([0-9`a-f]+)\s+\-)?"   # optional{ space (sBlockStartAddress) space (sBlockSize) space "-" }
        r"\s+([0-9`a-f]+)\s+([0-9`a-f]+)"             # space (sAllocationStartAddress) space (sAllocationSize)
        r"\s*$",                                      # [space]
        asPageHeapOutput[3],
      );
      assert oBlockInformationMatch, \
          "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asPageHeapOutput);
      sBlockStartAddress, sBlockSize, sAllocationStartAddress, sAllocationSize = oBlockInformationMatch.groups();
      uAllocationStartAddress = long(sAllocationStartAddress.replace("`", ""), 16);
      uAllocationSize = long(sAllocationSize.replace("`", ""), 16) - oCdbWrapper.oCurrentProcess.uPageSize; # Total size = allocation size + guard page size
    oVirtualAllocation = cVirtualAllocation.foGetForAddress(oCdbWrapper, uAllocationStartAddress);
    uPointerSize = oCdbWrapper.oCurrentProcess.uPointerSize;
    if bAllocated:
      uBlockStartAddress = long(sBlockStartAddress.replace("`", ""), 16);
      uBlockSize = long(sBlockSize.replace("`", ""), 16);
    elif oVirtualAllocation.bAllocated:
      # sBlockStartAddress and sBlockSize are None, but page heap did not actually free the page; it was made
      # inaccessible and so the block start address and size can be extracted from the page heap struct stored there.
      # The virtual allocation should start with 4 pointer sized values with unknown meaning, followed by pointer sized
      # 0 values, followed by the page heap structure and the heap block. We'll find the page heap struct by looking
      # for the first non-zero value after the 4 pointer sized unknown values:
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
      uHeapAddressOffset = uStartStampOffset + uPointerSize;     # ULONG StartStamp (with optional padding to pointer size)
      uRequestedSizeOffset = uHeapAddressOffset + uPointerSize;  # PVOID Heap
      uActualSizeOffset = uRequestedSizeOffset + uPointerSize;   # size_t RequestedSize
      uFreeQueueOffset = uActualSizeOffset + uPointerSize;       # size_t ActualSize
      uStackTraceOffset = uFreeQueueOffset + 2 * uPointerSize;   # LIST_ENTRY FreeQueue
      uEndStampOffset = uStackTraceOffset + uPointerSize;        # PVOID StackTrace
      uBlockStartOffset = uEndStampOffset + uPointerSize;        # ULONG EndStamp (with optional padding to pointer size)
      # Calculate the start address of the block based on the end offset of the full heap structure
      uBlockStartAddress = oVirtualAllocation.uBaseAddress + uBlockStartOffset;
      # Get the size of the block from the full heap structure
      uBlockSize = oVirtualAllocation.fuGetValueAtOffset(uRequestedSizeOffset, uPointerSize);
    else:
      uBlockStartAddress = uBlockSize = None; # This information was discarded, so we cannot report it.
    return cPageHeapAllocation(oVirtualAllocation, asPageHeapOutput, bAllocated, uAllocationStartAddress, uAllocationSize, uBlockStartAddress, uBlockSize);
  
  def __init__(oPageHeapAllocation, oVirtualAllocation, asPageHeapOutput, bAllocated, uAllocationStartAddress, uAllocationSize, \
      uBlockStartAddress, uBlockSize):
    uPointerSize = oVirtualAllocation.oProcess.uPointerSize;
    oPageHeapAllocation.oVirtualAllocation = oVirtualAllocation;
    oPageHeapAllocation.asPageHeapOutput = asPageHeapOutput;
    oPageHeapAllocation.bAllocated = bAllocated;
    oPageHeapAllocation.bFreed = not bAllocated;
    oPageHeapAllocation.uAllocationStartAddress = uAllocationStartAddress;
    oPageHeapAllocation.uAllocationSize = uAllocationSize;
    oPageHeapAllocation.bPageHeap = uAllocationStartAddress is not None;
    oPageHeapAllocation.uAllocationEndAddress = oPageHeapAllocation.bPageHeap and uAllocationStartAddress + uAllocationSize or None;
    oPageHeapAllocation.uBlockStartAddress = uBlockStartAddress;
    oPageHeapAllocation.uBlockSize = uBlockSize;
    if oPageHeapAllocation.uBlockStartAddress:
      oPageHeapAllocation.uBlockEndAddress = uBlockStartAddress and uBlockStartAddress + uBlockSize;
      # The heap block is pointer aligned, and allocated right before a guard page, at the end of the allocation.
      oPageHeapAllocation.uPostBlockPaddingSize = oPageHeapAllocation.bPageHeap \
          and oPageHeapAllocation.uAllocationEndAddress - oPageHeapAllocation.uBlockEndAddress or 0;
      # https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
      oPageHeapAllocation.uEndStampAddress = oPageHeapAllocation.uBlockStartAddress - uPointerSize;         # ULONG with optional padding to pointer size
      oPageHeapAllocation.uStackTraceAddress = oPageHeapAllocation.uEndStampAddress - uPointerSize;         # PVOID
      oPageHeapAllocation.uFreeQueueAddress = oPageHeapAllocation.uStackTraceAddress - 2 * uPointerSize;    # LIST_ENTRY
      oPageHeapAllocation.uActualSizeAddress = oPageHeapAllocation.uFreeQueueAddress - uPointerSize;        # size_t
      oPageHeapAllocation.uRequestedSizeAddress = oPageHeapAllocation.uActualSizeAddress - uPointerSize;    # size_t
      oPageHeapAllocation.uHeapAddressAddress = oPageHeapAllocation.uRequestedSizeAddress - uPointerSize;   # PVOID
      oPageHeapAllocation.uStartStampAddress = oPageHeapAllocation.uHeapAddressAddress - uPointerSize;      # ULONG with optional padding to pointer size
  
  def fatxMemoryRemarks(oPageHeapAllocation):
    uPointerSize = oPageHeapAllocation.oVirtualAllocation.oProcess.uPointerSize;
    atxMemoryRemarks = [];
    if oPageHeapAllocation.bPageHeap:
      atxMemoryRemarks.extend([
        ("Allocation start", oPageHeapAllocation.uAllocationStartAddress, None),
        ("Allocation end", oPageHeapAllocation.uAllocationEndAddress, None),
      ]);
    if oPageHeapAllocation.uBlockStartAddress:
      uStampPaddingSize = uPointerSize - 4;
      atxMemoryRemarks += [tx for tx in [
        ("Page heap ULONG start_stamp", oPageHeapAllocation.uStartStampAddress, None),
        uStampPaddingSize and \
            ("Page heap BYTE[%d] start_stamp_padding" % uStampPaddingSize, oPageHeapAllocation.uStartStampAddress + 4, None)
            or None,
        ("Page heap PVOID heap_address", oPageHeapAllocation.uHeapAddressAddress, None),
        ("Page heap size_t requested_size", oPageHeapAllocation.uRequestedSizeAddress, None),
        ("Page heap size_t actual_size", oPageHeapAllocation.uActualSizeAddress, None),
        ("Page heap LIST_ENTRY free_queue.FLink", oPageHeapAllocation.uFreeQueueAddress + uPointerSize, None),
        ("Page heap LIST_ENTRY free_queue.BLink", oPageHeapAllocation.uFreeQueueAddress, None),
        ("Page heap PVOID stack_trace", oPageHeapAllocation.uStackTraceAddress, None),
        uStampPaddingSize and \
            ("Page heap BYTE[%d] end_stamp_padding" % uStampPaddingSize, oPageHeapAllocation.uEndStampAddress, None) \
            or None,
        ("Page heap ULONG end_stamp", oPageHeapAllocation.uEndStampAddress, None),
        ("Memory block start", oPageHeapAllocation.uBlockStartAddress, None),
        ("Memory block end", oPageHeapAllocation.uBlockEndAddress, None),
        oPageHeapAllocation.uPostBlockPaddingSize and \
            ("Page heap BYTE[%d] post_block_padding", oPageHeapAllocation.uPostBlockPaddingSize, None)
            or None,
      ] if tx];
    return atxMemoryRemarks;
  
  def foCheckForCorruption(oPageHeapAllocation):
    uPointerSize = oPageHeapAllocation.oVirtualAllocation.oProcess.uPointerSize;
    oCorruptionDetector = cCorruptionDetector(oPageHeapAllocation.oVirtualAllocation);
    if oPageHeapAllocation.uBlockStartAddress:
      uStampPaddingSize = uPointerSize - 4;
      # Check start stamp and optional padding after start stamp
      axStartStamp = [[0xBA, 0xBB], 0xBB, 0xCD, 0xAB] + [0 for x in xrange(uStampPaddingSize)];
      oCorruptionDetector.fbDetectCorruption(oPageHeapAllocation.uStartStampAddress, axStartStamp);
      # Check optional padding before end stamp and end stamp itself
      axEndStamp = [0 for x in xrange(uStampPaddingSize)] + [[0xBA, 0xBB], 0xBB, 0xBA, 0xDC];
      oCorruptionDetector.fbDetectCorruption(oPageHeapAllocation.uEndStampAddress, axEndStamp);
      # Check optional padding after block
      if oPageHeapAllocation.uPostBlockPaddingSize:
        axPostBlockPadding = [0xD0 for x in xrange(oPageHeapAllocation.uPostBlockPaddingSize)]
        oCorruptionDetector.fbDetectCorruption(oPageHeapAllocation.uBlockEndAddress, axPostBlockPadding);
    return oCorruptionDetector.bCorruptionDetected and oCorruptionDetector or None;