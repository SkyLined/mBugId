import re;

from mWindowsAPI import *;

from .cPageHeapManagerData import cPageHeapManagerData;
from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;

grbIgnoredHeapOutputLines = re.compile(
  rb"^\s*"                                  # optional whitepsace
  rb"(?:"                                   # either {
    rb"ReadMemory error for address [0-9`a-f]+"
  rb"|"                                     # } or {
    rb"Use `!address [0-9`a-f]+' to check validity of the address."
  rb"|"                                     # } or {
    rb"\*\*\*.*\*\*\*"
  rb"|"                                     # } or {
    rb"unable to resolve ntdll!RtlpStackTraceDataBase"
  rb")"                                     # }
  rb"\s*$"                                  # optional whitespace
);

grbHeapOutputFirstLine = re.compile(
  rb"^\s+"                                  # whitespace
  rb"address [0-9`a-f]+ found in"           # "address " <address> " found in"
  rb"\s*$"                                  # optional whitepsace
);
grHeapOutputTypeAndRootAddressLine = re.compile(
  rb"^\s+"                                  #   whitespace
  rb"(_HEAP|_DPH_HEAP_ROOT)"                # * "_HEAP" or "_DPH_HEAP_ROOT"
  rb" @ "                                   #   " @ "
  rb"([0-9`a-f]+)"                          # * root-address
  rb"\s*$"                                  #   optional whitepsace
);
grbWindowsHeapInformationHeader = re.compile( # line #3
  rb"^\s+"                                  # whitespace
  rb"HEAP_ENTRY"                  rb"\s+"   # "HEAP_ENTRY"      whitespace
  rb"Size"                        rb"\s+"   # "Size"            whitespace
  rb"Prev"                        rb"\s+"   # "Prev"            whitespace
  rb"Flags"                       rb"\s+"   # "Flags"           whitespace
  rb"UserPtr"                     rb"\s+"   # "UserPtr"         whitespace
  rb"UserSize"                    rb"\s+"   # "UserSize"        whitespace
  rb"\-"                          rb"\s+"   # "-"               whitespace
  rb"state"                                 # "state" 
  rb"\s*$"                                  # optional whitespace
);

grbWindowsHeapInformation = re.compile(     # line #4
  rb"^\s+"                                  #   whitespace
  rb"([0-9`a-f]+)"                rb"\s+"   # * heap_entry_address whitespace
  rb"([0-9`a-f]+)"                rb"\s+"   # * heap_entry_size
  rb"[0-9`a-f]+"                  rb"\s+"   #   prev
  rb"\[" rb"[0-9`a-f]+" rb"\]"    rb"\s+"   #   "[" flags "]"
  rb"([0-9`a-f]+)"                rb"\s+"   # * sBlockStartAddress
  rb"([0-9`a-f]+)"                rb"\s+"   # * sBlockSize
  rb"\-"                          rb"\s+"   #   "-"
  rb"\(" rb"(busy|free|DelayedFree)" rb"\)" #* "(" state  ")"
  rb"\s*$"                                  # optional whitespace
);

grbDPHHeapInformationHeader = re.compile(   # line #3
  rb"^\s+"                                  #   whitespace
  rb"in"                          rb"\s+"   #   "in"                whitespace
  rb"(free-ed|busy)"              rb"\s+"   # * state               whitespace
  rb"allocation"                  rb"\s+"   #   "allocation"        whitespace
  rb"\("                          rb"\s*"   #   "("                 optional whitespace
  rb"DPH_HEAP_BLOCK:"             rb"\s+"   #   "DPH_HEAP_BLOCK:"   whitespace
  rb"(?:"                                   #   optional{
    rb"UserAddr"                  rb"\s+"   #     "UserAddr"        whitespace
    rb"UserSize"                  rb"\s+"   #     "UserSize"        whitespace
    rb"\-"                        rb"\s+"   #     "-"               whitespace
  rb")?"                                    #   }
  rb"VirtAddr"                    rb"\s+"   #   "VirtAddr"          whitespace
  rb"VirtSize"                    rb"\s*"   #   "VirtSize"          optional whitespace
  rb"\)"                                    #   ")"                 
  rb"\s*$",                                 # optional whitespace
);
grbDPHHeapInformation = re.compile(         # line #4
  rb"^\s+"                                  #   whitespace
  rb"([0-9`a-f]+)" rb":"  rb"\s+"           # * heap_header_address ":"   whitespace
  rb"(?:"                                   #   optional {
    rb"([0-9`a-f]+)"     rb"\s+"            # *   sBlockStartAddress      whitespace
    rb"([0-9`a-f]+)"     rb"\s+"            # *   sBlockSize              whitespace
    rb"\-"               rb"\s+"            #     "-"                     whitespace
  rb")?"                                    #   }
  rb"([0-9`a-f]+)"       rb"\s+"            # * sAllocationStartAddress   whitespace
  rb"([0-9`a-f]+)"                          # * sAllocationSize
  rb"\s*$"                                  # optional whitespace
);

def cProcess_fo0GetHeapManagerDataForAddress(oProcess, uAddress, sType):
  sType = sType or "unknown";
  # Strip warnings and errors that we may be able to ignore:
  asbCdbHeapOutput = [
    sbLine
    for sbLine in oProcess.fasbExecuteCdbCommand(
      sbCommand = b"!heap -p -a 0x%X;" % uAddress,
      sb0Comment = b"Get page heap information",
      bOutputIsInformative = True,
    )
    if not grbIgnoredHeapOutputLines.match(sbLine)
  ];
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
  
  if len(asbCdbHeapOutput) < 4:
    # No !heap output; make sure it is enabled for this process.
    oProcess.fEnsurePageHeapIsEnabled();
    # Try to manually figure things out.
    try:
      return cPageHeapManagerData.fo0GetForProcessAndAddress(oProcess, uAddress);
    except AssertionError:
      # That didn't work; we have no information about a heap block at this address.
      return None;
  assert grbHeapOutputFirstLine.match(asbCdbHeapOutput[0]), \
      "Unrecognized page heap report first line:\r\n%s" % "\r\n".join(asbCdbHeapOutput);
  obHeapOutputTypeAndRootAddressMatch = grHeapOutputTypeAndRootAddressLine.match(asbCdbHeapOutput[1]);
  assert obHeapOutputTypeAndRootAddressMatch, \
      "Unrecognized page heap report second line:\r\n%s" % "\r\n".join(asbCdbHeapOutput);
  sbHeapType, sbHeapRootAddress = obHeapOutputTypeAndRootAddressMatch.groups();
  uHeapRootAddress = fu0ValueFromCdbHexOutput(sbHeapRootAddress);
  if sbHeapType == b"_HEAP":
    assert sType in ["windows", "unknown"], \
        "Expected heap allocator to be %s, but found default windows allocator" % sType;
    # Regular Windows heap.
    assert grbWindowsHeapInformationHeader.match(asbCdbHeapOutput[2]), \
        "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(absCdbHeapOutput);
    obBlockInformationMatch = grbWindowsHeapInformation.match(asCdbHeapOutput[3]);
    assert obBlockInformationMatch, \
        "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asbCdbHeapOutput);
    (
      sbHeapEntryStartAddress,
      sbHeapEntrySizeInPointers,
      sbBlockStartAddress,
      sbBlockSize,
      sbState,
    ) = obBlockInformationMatch.groups();
    uHeapEntryStartAddress = fu0ValueFromCdbHexOutput(sbHeapEntryStartAddress);
    uHeapEntrySize = fu0ValueFromCdbHexOutput(sbHeapEntrySizeInPointers) * oProcess.uPointerSize;
    u0HeapBlockStartAddress = fu0ValueFromCdbHexOutput(sbBlockStartAddress);
    u0HeapBlockSize = fu0ValueFromCdbHexOutput(sbBlockSize);
    bAllocated = sbState == b"busy";
    oVirtualAllocation = cVirtualAllocation(oProcess.uId, u0HeapBlockStartAddress);
    assert oVirtualAllocation, \
      "Cannot find virtual allocation for heap block at 0x%X" % u0HeapBlockStartAddress;
    from .cWindowsHeapManagerData import cWindowsHeapManagerData;
    oHeapManagerData = cWindowsHeapManagerData(
      oVirtualAllocation,
      uHeapEntryStartAddress,
      uHeapEntrySize,
      u0HeapBlockStartAddress,
      u0HeapBlockSize,
      bAllocated,
    );
  else:
    assert sType in ["page heap", "unknown"], \
        "Expected heap allocator to be %s, but found page heap allocator" % sType;
    obDPHHeapInformationHeaderMatch = grbDPHHeapInformationHeader.match(asbCdbHeapOutput[2]);
    assert obDPHHeapInformationHeaderMatch, \
        "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asbCdbHeapOutput);
    sbState = obDPHHeapInformationHeaderMatch.group(1);
    bAllocated = sbState == b"busy";
    obBlockInformationMatch = grbDPHHeapInformation.match(asbCdbHeapOutput[3]);
    assert obBlockInformationMatch, \
        "Unrecognized page heap report fourth line:\r\n%s" % "\r\n".join(asbCdbHeapOutput);
    (
      sbAllocationInformationStartAddress,
      sb0HeapBlockStartAddress,
      sb0HeapBlockSize,
      sbVirtualAllocationStartAddress,
      sbVirtualAllocationSize,
    ) = obBlockInformationMatch.groups();
    uAllocationInformationStartAddress = fu0ValueFromCdbHexOutput(sbAllocationInformationStartAddress)
    uVirtualAllocationStartAddress = fu0ValueFromCdbHexOutput(sbVirtualAllocationStartAddress);
    uVirtualAllocationSize = fu0ValueFromCdbHexOutput(sbVirtualAllocationSize);
    u0HeapBlockStartAddress = fu0ValueFromCdbHexOutput(sb0HeapBlockStartAddress);
    u0HeapBlockSize = fu0ValueFromCdbHexOutput(sb0HeapBlockSize);
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
        (sbState, oHeapManagerData.bAllocated and "allocated" or "free", \
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
  if u0HeapBlockStartAddress is not None:
    assert u0HeapBlockStartAddress == oHeapManagerData.uHeapBlockStartAddress, \
        "Page heap block start address (@ 0x%X) is different than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.uHeapBlockStartAddress, u0HeapBlockStartAddress);
    assert u0HeapBlockSize == oHeapManagerData.uHeapBlockSize, \
        "Page heap block size (0x%X) is different than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.uHeapBlockSize, u0HeapBlockSize);
  return oHeapManagerData;
