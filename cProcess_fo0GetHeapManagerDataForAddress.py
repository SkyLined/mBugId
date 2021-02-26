import re;
from mWindowsAPI import *;
from .cPageHeapManagerData import cPageHeapManagerData;

def cProcess_fo0GetHeapManagerDataForAddress(oProcess, uAddress, sType):
  sType = sType or "unknown";
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
    # No !heap output; make sure it is enabled for this process.
    oProcess.fEnsurePageHeapIsEnabled();
    # Try to manually figure things out.
    try:
      return cPageHeapManagerData.fo0GetForProcessAndAddress(oProcess, uAddress);
    except AssertionError:
      # That didn't work; we have no information about a heap block at this address.
      return None;
  
  assert re.match(r"^\s+address [0-9`a-f]+ found in\s*$", asCdbHeapOutput[0]), \
      "Unrecognized page heap report first line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
  oHeapTypeMatch = re.match(r"^\s+(_HEAP|_DPH_HEAP_ROOT) @ ([0-9`a-f]+)\s*$", asCdbHeapOutput[1]);
  assert oHeapTypeMatch, \
      "Unrecognized page heap report second line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
  sHeapType, sHeapRootAddress = oHeapTypeMatch.groups();
  uHeapRootAddress = long(sHeapRootAddress.replace("`", ""), 16);
  if sHeapType == "_HEAP":
    assert sType in ["windows", "unknown"], \
        "Expected heap allocator to be %s, but found default windows allocator" % sType;
    # Regular Windows heap.
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
        r"\(" r"(busy|free|DelayedFree)" r"\)",   # "(" (sState)  ")"
      ]),
      asCdbHeapOutput[3],
    );
    assert oBlockInformationMatch, \
        "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
    (
      sHeapEntryStartAddress,
      sHeapEntrySizeInPointers,
      sBlockStartAddress,
      sBlockSize,
      sState,
    ) = oBlockInformationMatch.groups();
    uHeapEntryStartAddress = long(sHeapEntryStartAddress.replace("`", ""), 16);
    uHeapEntrySize = long(sHeapEntrySizeInPointers.replace("`", ""), 16) * oProcess.uPointerSize;
    uHeapBlockStartAddress = long(sBlockStartAddress.replace("`", ""), 16);
    uHeapBlockSize = long(sBlockSize.replace("`", ""), 16);
    bAllocated = sState == "busy";
    oVirtualAllocation = cVirtualAllocation(oProcess.uId, uHeapBlockStartAddress);
    assert oVirtualAllocation, \
      "Cannot find virtual allocation for heap block at 0x%X" % uHeapBlockStartAddress;
    from cWindowsHeapManagerData import cWindowsHeapManagerData;
    oHeapManagerData = cWindowsHeapManagerData(
      oVirtualAllocation,
      uHeapEntryStartAddress,
      uHeapEntrySize,
      uHeapBlockStartAddress,
      uHeapBlockSize,
      bAllocated,
    );
  else:
    assert sType in ["page heap", "unknown"], \
        "Expected heap allocator to be %s, but found page heap allocator" % sType;
    oDPHHeapBlockTypeMatch = re.match(  # line #3
      r"^"                  r"\s*"      # {                         [whitespace]
      r"in"                 r"\s+"      #   "in"                     whitespace
      r"(free-ed|busy)"     r"\s+"      #   (sState)                 whitespace
      r"allocation"         r"\s+"      #   "allocation"             whitespace
      r"\("                 r"\s*"      #   "("                     [whitespace]
        r"DPH_HEAP_BLOCK:"  r"\s+"      #     "DPH_HEAP_BLOCK:"      whitespace
        r"(?:"                          #     optional{
          r"UserAddr"       r"\s+"      #       "UserAddr"           whitespace
          r"UserSize"       r"\s+"      #       "UserSize"           whitespace
          r"\-"             r"\s+"      #       "-"                  whitespace
        r")?"                           #     }
        r"VirtAddr"         r"\s+"      #     "VirtAddr"             whitespace
        r"VirtSize"         r"\s*"      #     "VirtSize"            [whitespace]
      r"\)"                 r"\s*"      #   ")"                     [whitespace]
      r"$",                             # }
      asCdbHeapOutput[2],
    );
    assert oDPHHeapBlockTypeMatch, \
        "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
    sState = oDPHHeapBlockTypeMatch.group(1);
    bAllocated = sState == "busy";
    oBlockInformationMatch = re.match(  # line #4
      r"^"                  r"\s*"      # {                         [whitespace]
      r"([0-9`a-f]+)" r":"  r"\s+"      #   heap_header_address ":"  whitespace
      r"(?:"                            #   optional {
        r"([0-9`a-f]+)"     r"\s+"      #     (sBlockStartAddress)   whitespace
        r"([0-9`a-f]+)"     r"\s+"      #     (sBlockSize)           whitespace
        r"\-"               r"\s+"      #     "-"                    whitespace
      r")?"                             #   }
      r"([0-9`a-f]+)"       r"\s+"      #   (sAllocationStartAddress) whitespace
      r"([0-9`a-f]+)"       r"\s*"      #   sAllocationSize         [whitespace]
      r"$",                             # }
      asCdbHeapOutput[3],
    );
    assert oBlockInformationMatch, \
        "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asCdbHeapOutput);
    (
      sAllocationInformationStartAddress,
      sHeapBlockStartAddress,
      sHeapBlockSize,
      sVirtualAllocationStartAddress,
      sVirtualAllocationSize,
    ) = oBlockInformationMatch.groups();
    uAllocationInformationStartAddress = long(sAllocationInformationStartAddress.replace("`", ""), 16)
    uVirtualAllocationStartAddress = long(sVirtualAllocationStartAddress.replace("`", ""), 16);
    uVirtualAllocationSize = long(sVirtualAllocationSize.replace("`", ""), 16);
    uHeapBlockStartAddress = sHeapBlockStartAddress and long(sHeapBlockStartAddress.replace("`", ""), 16);
    uHeapBlockSize = sHeapBlockSize and long(sHeapBlockSize.replace("`", ""), 16);
    o0HeapManagerData = cPageHeapManagerData.fo0GetForProcessAndAllocationInformationStartAddress(
      oProcess,
      uAllocationInformationStartAddress,
    );
    if not o0HeapManagerData:
      return None;
    oHeapManagerData = o0HeapManagerData;
    oHeapManagerData.uHeapRootAddress = uHeapRootAddress;
    assert bAllocated == oHeapManagerData.bAllocated, \
        "cdb says block is %s, but page heap allocation information says %s" % \
        (sState, oHeapManagerData.bAllocated and "allocated" or "free", \
        uExpectedState, "\r\n".join(asCdbHeapOutput));
    assert uVirtualAllocationStartAddress == oHeapManagerData.oVirtualAllocation.uStartAddress, \
        "Page heap allocation found at a different address (@ 0x%X) than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.oVirtualAllocation.uStartAddress, uVirtualAllocationStartAddress);
# Page heap may report a larger virtual allocation size when there is an allocation that contains the heap block
# followed by a (reserved, non-accessible) canary allocation (in order to trigger an AV when code attempts to read OOB
# data). Once the memory is freed, it is replaced by one big reserved allocation. This makes sanity checking the size
# more complex than I'm interested in implementing.
#    assert uVirtualAllocationSize == oHeapManagerData.oVirtualAllocation.uSize, \
#        "Page heap allocation at 0x%X has different size (0x%X) than reported by cdb (@ 0x%X)" % \
#        (oHeapManagerData.oVirtualAllocation.uStartAddress, oHeapManagerData.oVirtualAllocation.uSize, \
#        uVirtualAllocationSize);
    assert uAllocationInformationStartAddress == oHeapManagerData.uAllocationInformationStartAddress, \
        "Page heap allocation header points to different information (@ 0x%X) than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.uAllocationInformationStartAddress, uAllocationInformationStartAddress);
  if uHeapBlockStartAddress is not None:
    assert uHeapBlockStartAddress == oHeapManagerData.uHeapBlockStartAddress, \
        "Page heap block start address (@ 0x%X) is different than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.uHeapBlockStartAddress, uHeapBlockStartAddress);
    assert uHeapBlockSize == oHeapManagerData.uHeapBlockSize, \
        "Page heap block size (0x%X) is different than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.uHeapBlockSize, uHeapBlockSize);
  return oHeapManagerData;
