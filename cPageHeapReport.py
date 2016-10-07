import re;

class cPageHeapReport(object):
  @staticmethod
  def foCreate(oCdbWrapper, uAddress):
    # This is not a special marker or NULL, so it must be an invalid pointer
    # See is page heap has more details on the address at which the access violation happened:
    asPageHeapOutput = oCdbWrapper.fasSendCommandAndReadOutput(
      "!heap -p -a 0x%X; $$ Get page heap information" % uAddress,
      bOutputIsInformative = True,
    );
    if not oCdbWrapper.bCdbRunning: return;
    uPointerSize = oCdbWrapper.fuGetValue("$ptrsize");
    if not oCdbWrapper.bCdbRunning: return;
    uPageSize = oCdbWrapper.fuGetValue("$pagesize");
    if not oCdbWrapper.bCdbRunning: return;
    # Sample output:
    # |    address 0e948ffc found in
    # |    _DPH_HEAP_ROOT @ 48b1000
    # |    in free-ed allocation (  DPH_HEAP_BLOCK:         VirtAddr         VirtSize)
    # |                                    e9f08bc:          e948000             2000
    # |    6d009cd2 verifier!AVrfDebugPageHeapFree+0x000000c2
    # |    77d42e20 ntdll!RtlDebugFreeHeap+0x0000003c
    # |    77cfe0da ntdll!RtlpFreeHeap+0x0006c97a
    # |    77cf5d2c ntdll!RtlpFreeHeapInternal+0x0000027e
    # |    77c90a3c ntdll!RtlFreeHeap+0x0000002c
    # <<<snip>>> no 0-day information for you!
    # |    address 07fd1000 found in
    # |    _DPH_HEAP_ROOT @ 4fd1000
    # |    in busy allocation (  DPH_HEAP_BLOCK:         UserAddr         UserSize -         VirtAddr         VirtSize)
    # |                                 7f51d9c:          7fd0fc0               40 -          7fd0000             2000
    # |    6c469abc verifier!AVrfDebugPageHeapAllocate+0x0000023c
    # <<<snip>>> no 0-day information for you!
    # There may be errors, sample output:
    # |ReadMemory error for address 5b59c3d0
    # |Use `!address 5b59c3d0' to check validity of the address.
    # <<<snip>>>
    # |*************************************************************************
    # |***                                                                   ***
    # |***                                                                   ***
    # |***    Either you specified an unqualified symbol, or your debugger   ***
    # |***    doesn't have full symbol information.  Unqualified symbol      ***
    # |***    resolution is turned off by default. Please either specify a   ***
    # |***    fully qualified symbol module!symbolname, or enable resolution ***
    # <<<snip>>>
    # unable to resolve ntdll!RtlpStackTraceDataBase
    
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
    assert re.match(r"^\s+\w+ @ [0-9`a-f]+\s*$", asPageHeapOutput[1]), \
        "Unrecognized page heap report second line:\r\n%s" % "\r\n".join(asPageHeapOutput);
    oBlockTypeMatch = re.match(                       # line #3
        r"^\s+in (free-ed|busy) allocation \("        # space "in" space ("free-ed" | "busy") space  "allocation ("
        r"\s*\w+:"                                    #   [space] DPH_HEAP_BLOCK ":"
        r"(?:\s+UserAddr\s+UserSize\s+\-)?"           #   optional{ space "UserAddr" space "UserSize" space "-" }
        r"\s+VirtAddr\s+VirtSize"                     #   space "VirtAddr" space "VirtSize"
        r"\)\s*$",                                    # ")" [space]
        asPageHeapOutput[2]);
    assert oBlockTypeMatch, \
        "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asPageHeapOutput);
    oBlockAdressAndSizeMatch = re.match(              # line #4
        r"^\s+[0-9`a-f]+:"                            # space heap_header_address ":"
        r"(?:\s+([0-9`a-f]+)\s+([0-9`a-f]+)\s+\-)?"   # optional{ space (heap_block_address) space (heap_block_size) space "-" }
        r"\s+([0-9`a-f]+)\s+([0-9`a-f]+)"                 # space heap_pages_address space heap_pages_size
        r"\s*$",                                      # [space]
        asPageHeapOutput[3]);
    assert oBlockAdressAndSizeMatch, \
        "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asPageHeapOutput);
    sBlockType = oBlockTypeMatch.group(1);
    sBlockAddress, sBlockSize, sAllocationAddress, sTotalSize = oBlockAdressAndSizeMatch.groups();
    uAllocationAddress = long(sAllocationAddress.replace("`", ""), 16);
    uAllocationSize = long(sTotalSize.replace("`", ""), 16) - uPageSize; # Total size = allocation size + guard page size
    uBlockAddress = sBlockAddress and long(sBlockAddress.replace("`", ""), 16);
    uBlockSize = sBlockSize and long(sBlockSize.replace("`", ""), 16);
    return cPageHeapReport(asPageHeapOutput, uPointerSize, sBlockType, uAllocationAddress, uAllocationSize, uBlockAddress, uBlockSize);
  
  def __init__(oPageHeapReport, asPageHeapOutput, uPointerSize, sBlockType, uAllocationStartAddress, uAllocationSize, \
      uBlockStartAddress, uBlockSize):
    oPageHeapReport.asPageHeapOutput = asPageHeapOutput;
    oPageHeapReport.uPointerSize = uPointerSize;
    oPageHeapReport.sBlockType = sBlockType;
    oPageHeapReport.uAllocationStartAddress = uAllocationStartAddress;
    oPageHeapReport.uAllocationSize = uAllocationSize;
    oPageHeapReport.uAllocationEndAddress = uAllocationStartAddress + uAllocationSize;
    oPageHeapReport.uBlockStartAddress = uBlockStartAddress;
    oPageHeapReport.uBlockSize = uBlockSize;
    if oPageHeapReport.uBlockStartAddress:
      oPageHeapReport.uBlockEndAddress = uBlockStartAddress and uBlockStartAddress + uBlockSize;
      # The heap block is pointer aligned, and allocated right before a guard page, at the end of the allocation.
      oPageHeapReport.uPostBlockPaddingSize = oPageHeapReport.uAllocationEndAddress - oPageHeapReport.uBlockEndAddress;
      # https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
      oPageHeapReport.uEndStampAddress = oPageHeapReport.uBlockStartAddress - uPointerSize;         # ULONG with optional padding to pointer size
      oPageHeapReport.uStackTraceAddress = oPageHeapReport.uEndStampAddress - uPointerSize;         # PVOID
      oPageHeapReport.uFreeQueueAddress = oPageHeapReport.uStackTraceAddress - 2 * uPointerSize;    # LIST_ENTRY
      oPageHeapReport.uActualSizeAddress = oPageHeapReport.uFreeQueueAddress - uPointerSize;        # size_t
      oPageHeapReport.uRequestedSizeAddress = oPageHeapReport.uActualSizeAddress - uPointerSize;    # size_t
      oPageHeapReport.uHeapAddressAddress = oPageHeapReport.uRequestedSizeAddress - uPointerSize;   # PVOID
      oPageHeapReport.uStartStampAddress = oPageHeapReport.uHeapAddressAddress - uPointerSize;      # ULONG with optional padding to pointer size
  
  def fatxMemoryRemarks(oPageHeapReport):
    atxMemoryRemarks = [
      ("Allocation start", oPageHeapReport.uAllocationStartAddress, None),
      ("Allocation end", oPageHeapReport.uAllocationEndAddress, None),
    ];
    if oPageHeapReport.uBlockStartAddress:
      uStampPaddingSize = oPageHeapReport.uPointerSize - 4;
      atxMemoryRemarks += [tx for tx in [
        ("Page heap ULONG start_stamp", oPageHeapReport.uStartStampAddress, None),
        uStampPaddingSize and \
            ("Page heap BYTE[%d] start_stamp_padding" % uStampPaddingSize, oPageHeapReport.uStartStampAddress + 4, None)
            or None,
        ("Page heap PVOID heap_address", oPageHeapReport.uHeapAddressAddress, None),
        ("Page heap size_t requested_size", oPageHeapReport.uRequestedSizeAddress, None),
        ("Page heap size_t actual_size", oPageHeapReport.uActualSizeAddress, None),
        ("Page heap LIST_ENTRY free_queue.FLink", oPageHeapReport.uFreeQueueAddress + oPageHeapReport.uPointerSize, None),
        ("Page heap LIST_ENTRY free_queue.BLink", oPageHeapReport.uFreeQueueAddress, None),
        ("Page heap PVOID stack_trace", oPageHeapReport.uStackTraceAddress, None),
        uStampPaddingSize and \
            ("Page heap BYTE[%d] end_stamp_padding" % uStampPaddingSize, oPageHeapReport.uEndStampAddress, None) \
            or None,
        ("Page heap ULONG end_stamp", oPageHeapReport.uEndStampAddress, None),
        ("Memory block start", oPageHeapReport.uBlockStartAddress, None),
        ("Memory block end", oPageHeapReport.uBlockEndAddress, None),
        oPageHeapReport.uPostBlockPaddingSize and \
            ("Page heap BYTE[%d] post_block_padding", oPageHeapReport.uPostBlockPaddingSize, None)
            or None,
      ] if tx];
    return atxMemoryRemarks;
  
  def fbCheckForCorruption(oPageHeapReport, oCorruptionDetector):
    if oPageHeapReport.uBlockStartAddress:
      uStampPaddingSize = oPageHeapReport.uPointerSize - 4;
      # Check start stamp and optional padding after start stamp
      axStartStamp = [[0xBA, 0xBB], 0xBB, 0xCD, 0xAB] + [0 for x in xrange(uStampPaddingSize)];
      while len(axStartStamp) < oPageHeapReport.uPointerSize: axStartStamp.append(0);
      oCorruptionDetector.fbDetectCorruption(oPageHeapReport.uStartStampAddress, axStartStamp);
      # Check optional padding before end stamp and end stamp itself
      axEndStamp = [0 for x in xrange(uStampPaddingSize)] + [[0xBA, 0xBB], 0xBB, 0xBA, 0xDC];
      while len(axEndStamp) < oPageHeapReport.uPointerSize: axEndStamp.insert(0, 0);
      oCorruptionDetector.fbDetectCorruption(oPageHeapReport.uEndStampAddress, axEndStamp);
      # Check optional padding after block
      if oPageHeapReport.uPostBlockPaddingSize:
        axPostBlockPadding = [0xD0 for x in xrange(oPageHeapReport.uPostBlockPaddingSize)]
        oCorruptionDetector.fbDetectCorruption(oPageHeapReport.uBlockEndAddress, axPostBlockPadding);
    return oCorruptionDetector.bCorruptionDetected;