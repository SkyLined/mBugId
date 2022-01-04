import re;

from mWindowsAPI import *;

from ..cPageHeapManagerData import cPageHeapManagerData;
from ..dxConfig import dxConfig;
from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..mCP437 import fsCP437FromBytesString;

gbDebugOutput = False;

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

def cProcess_fo0GetHeapManagerDataForAddress(oProcess, uAddress, s0ExpectedType = None):
  if uAddress < dxConfig["uMaxAddressOffset"]:
    return None; # quick return for NULL pointers
  if uAddress >= (1 << ({"x86": 32, "x64": 64}[oProcess.sISA])):
    return None; # quick return for invalid addresses.
  # Page heap can keep freed heap blocks reserved in order to detect use-after-free and
  # keep information about the heap block. It also keeps a canary page reserved to detect
  # out-of-bounds reads. So, if the memory page is free, it cannot be a page heap block
  # that we can find information about.
  # Normal heaps are always either allocated, or freed. In the later case we cannot find
  # information about it.
  # In short, we can quickly determine if it makes sense to see if there is a heap block
  # at the given address, by checking if the virtual allocation at the address is valid 
  # and not free. We can also ignore virtual allocations that are executable, as heap
  # blocks are never executable under normal circumstances.
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, uAddress);
  if not oVirtualAllocation.bIsValid or oVirtualAllocation.bFree or oVirtualAllocation.bExecutable:
    return None;
  # Using "!heap -p -a 0x%X" can take quite a long time for addresses that do not point
  # near a valid page heap block. I believe the check on the virtual allocation above
  # should filter out all these cases, but I cannot guarantee it.
  # Our own page heap manager code can try to make sense of the page heap meta-data near
  # the address. It will throw an AssertionError if it believes the address is not part
  # of the page heap. Theoretically, random data could look like valid page heap meta
  # data and lead to incorrect results. However, I expect the chances of that happening
  # are really small and the time-savings are enormous, so I've opted to gamble:
  try:
    o0PageHeapManagerData = cPageHeapManagerData.fo0GetForProcessAndAddress(oProcess, uAddress);
  except AssertionError:
    # The address does not appear to point near a valid page heap backing page.
    bBugIdPageHeapManagerDataWasAbleToProcessData = False;
  else:
    bBugIdPageHeapManagerDataWasAbleToProcessData = True;
    if o0PageHeapManagerData:
      # The address appears to point near a valid page heap block.
      return o0PageHeapManagerData;
  # At this point I expect the memory to either point to a regular windows heap, or
  # non-free, non-heap memory. Let's ask cdb.exe what it thinks we are looking at:
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
    # That didn't work; we have no information about a heap block at this address.
    if gbDebugOutput: print("cProcess.fo0GetHeapManagerDataForAddress: Unrecognized !heap output: %s" % repr(asbCdbHeapOutput));
    return None;
  assert grbHeapOutputFirstLine.match(asbCdbHeapOutput[0]), \
      "Unrecognized page heap report first line:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbHeapOutput);
  obHeapOutputTypeAndRootAddressMatch = grHeapOutputTypeAndRootAddressLine.match(asbCdbHeapOutput[1]);
  assert obHeapOutputTypeAndRootAddressMatch, \
      "Unrecognized page heap report second line:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbHeapOutput);
  sbHeapType, sbHeapRootAddress = obHeapOutputTypeAndRootAddressMatch.groups();
  uHeapRootAddress = fu0ValueFromCdbHexOutput(sbHeapRootAddress);
  if sbHeapType == b"_HEAP":
    if gbDebugOutput: print("cProcess.fo0GetHeapManagerDataForAddress: detected regular heap");
    if s0ExpectedType is not None:
      assert s0ExpectedType == "windows", \
          "Expected heap allocator to be %s, but found default windows allocator" % s0ExpectedType;
    # Regular Windows heap.
    assert grbWindowsHeapInformationHeader.match(asbCdbHeapOutput[2]), \
        "Unrecognized page heap report third line:\r\n%s" % "\r\n".join(asbCdbHeapOutput);
    obBlockInformationMatch = grbWindowsHeapInformation.match(asbCdbHeapOutput[3]);
    assert obBlockInformationMatch, \
        "Unrecognized page heap report fourth line:\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbHeapOutput);
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
    oHeapManagerData = cWindowsHeapManagerData(
      oVirtualAllocation,
      uHeapEntryStartAddress,
      uHeapEntrySize,
      u0HeapBlockStartAddress,
      u0HeapBlockSize,
      bAllocated,
    );
  else:
    # If !heap -p can process this, we should have been able to process it too!
    if not bBugIdPageHeapManagerDataWasAbleToProcessData:
      cPageHeapManagerData.fo0GetForProcessAndAddress(oProcess, uAddress);
    assert bBugIdPageHeapManagerDataWasAbleToProcessData, \
          "BugId cPageHeapManagerData was unable to process what appears to be a valid page heap block:\n%s" % repr(asbCdbHeapOutput);
    if gbDebugOutput: print("cProcess.fo0GetHeapManagerDataForAddress: detected page heap");
    if s0ExpectedType is not None:
      assert s0ExpectedType == "page heap", \
          "Expected heap allocator to be %s, but found page heap allocator" % s0ExpectedType;
    obDPHHeapInformationHeaderMatch = grbDPHHeapInformationHeader.match(asbCdbHeapOutput[2]);
    assert obDPHHeapInformationHeaderMatch, \
        "Unrecognized page heap report third line:\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbHeapOutput);
    sbState = obDPHHeapInformationHeaderMatch.group(1);
    bAllocated = sbState == b"busy";
    obBlockInformationMatch = grbDPHHeapInformation.match(asbCdbHeapOutput[3]);
    assert obBlockInformationMatch, \
        "Unrecognized page heap report fourth line:\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbHeapOutput);
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
    if o0HeapManagerData is None:
      if gbDebugOutput: print("cProcess.fo0GetHeapManagerDataForAddress: nothing found at 0x%X in process %d/0x%X: returning None" % (
        uAllocationInformationStartAddress, oProcess.uId, oProcess.uId, 
       ));
      return None;
    oHeapManagerData = o0HeapManagerData;
    oHeapManagerData.uHeapRootAddress = uHeapRootAddress;
    assert bAllocated == oHeapManagerData.bAllocated, \
        "cdb says block is %s, but page heap allocation information says it is %s" % \
        (sbState, oHeapManagerData.bAllocated and "allocated" or "free");
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
  if gbDebugOutput: print("cProcess.fo0GetHeapManagerDataForAddress: returning %s" % repr(oHeapManagerData));
  return oHeapManagerData;

from ..cWindowsHeapManagerData import cWindowsHeapManagerData;
