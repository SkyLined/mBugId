import re;

from mWindowsAPI import cVirtualAllocation, oSystemInfo;

from ..mHeapManager import cWindowsHeapManagerData;
from ..dxConfig import dxConfig;
from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..mCP437 import fsCP437FromBytesString;

gbDebugOutput = True;

grbIgnoredHeapOutputLines = re.compile(
  rb"^\s*"                                  # optional whitespace
  rb"(?:"                                   # either {
    rb"ReadMemory error for address [0-9`a-f]+"
  rb"|"                                     # } or {
    rb"Use `!address [0-9`a-f]+' to check validity of the address."
  rb"|"                                     # } or {
    rb"\*\*\*.*\*\*\*"
  rb"|"                                     # } or {
    rb"unable to resolve ntdll!RtlpStackTraceDataBase"
  rb"|"                                     # } or { (nothing - empty line)
  rb")"                                     # }
  rb"\s*$"                                  # optional whitespace
);

grbHeapOutputFirstLine = re.compile(
  rb"^\s+"                                  # whitespace
  rb"address [0-9`a-f]+ found in"           # "address " <address> " found in"
  rb"\s*$"                                  # optional whitespace
);
grHeapOutputTypeAndRootAddressLine = re.compile(
  rb"^\s+"                                  #   whitespace
  rb"_HEAP"                                 #   "_HEAP"
  rb" @ "                                   #   " @ "
  rb"([0-9`a-f]+)"                          # * root-address
  rb"\s*$"                                  #   optional whitespace
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


# Sometimes we need to use "!heap", sometimes we need to use "!ext.heap"
# I do not know how to determine which one to use. Luckily, if we use
# "!heap" when we should be using "!ext.heap", cdb.ex will give us a
# warning, which we can detect and try again. If this happens, we'll set
# a global flag so we can skip trying "!heap" the next time:
# we'll try the first
gbUseExtHeap = False;

def cProcess_fo0GetWindowsHeapManagerDataForAddressNearHeapBlock(oProcess, uAddressNearHeapBlock):
  global gbUseExtHeap;
  if uAddressNearHeapBlock <= dxConfig["uMaxAddressOffset"]:
    return None; # Considered a NULL pointer;
  if uAddressNearHeapBlock >= (1 << ({"x86": 32, "x64": 64}[oProcess.sISA])):
    return None; # Value is not in the valid address range
  oVirtualAllocation = cVirtualAllocation(
    oProcess.uId,
    uAddressNearHeapBlock,
  );
  if oVirtualAllocation.bFree or oVirtualAllocation.bReserved:
    # The virtual allocation at the provided address is free or reserved.
    # in case of an out-of-bounds access that causes an access violation,
    # this is to be expected. If the offset from the start of the allocation
    # is less than one page, let's look at the previous allocation:
    uOffsetFromStartOfVirtualAllocation = uAddressNearHeapBlock - oVirtualAllocation.uStartAddress;
    if uOffsetFromStartOfVirtualAllocation < oSystemInfo.uPageSize:
      oPreviousVirtualAllocation = cVirtualAllocation(
        oProcess.uId,
        oVirtualAllocation.uStartAddress - 1,
      );
      if oPreviousVirtualAllocation.bAllocated:
        # Let's assume this is the allocation we are looking for:
        oVirtualAllocation = oPreviousVirtualAllocation;
        uAddressNearHeapBlock = oVirtualAllocation.uEndAddress - 1;
      else:
        # This could also be an out-of-bounds access _before_ the allocation
        # if the offset from the end of the allocation is less than one page.
        uOffsetFromEndOfVirtualAllocation = oVirtualAllocation.uEndAddress - uAddressNearHeapBlock;
        if uOffsetFromEndOfVirtualAllocation < oSystemInfo.uPageSize:
          oNextVirtualAllocation = cVirtualAllocation(
            oProcess.uId,
            oVirtualAllocation.uEndAddress,
          );
          if oNextVirtualAllocation.bAllocated:
            # Let's assume this is the allocation we are looking for:
            oVirtualAllocation = oNextVirtualAllocation;
            uAddressNearHeapBlock = oVirtualAllocation.uStartAddress;
          else:
            return None;
  # At this point I expect the memory to either point to a regular windows heap, or
  # non-free, non-heap memory. Let's ask cdb.exe what it thinks we are looking at:
  if not gbUseExtHeap:
    asbCdbHeapOutput = [
      sbLine
      for sbLine in oProcess.fasbExecuteCdbCommand(
        sbCommand = b"!heap -p -a 0x%X;" % uAddressNearHeapBlock,
        sb0Comment = b"Get heap information",
        bOutputIsInformative = True,
      )
      if not grbIgnoredHeapOutputLines.match(sbLine.strip())
    ];
    if asbCdbHeapOutput == [
      b"the `!heap -p' commands in exts.dll have been replaced",
      b"with equivalent commands in ext.dll.",
      b"If your are in a KD session, use `!ext.heap -p`",
    ]:
      gbUseExtHeap = True;
  if gbUseExtHeap:
    asbCdbHeapOutput = [
      sbLine
      for sbLine in oProcess.fasbExecuteCdbCommand(
        sbCommand = b"!ext.heap -p -a 0x%X;" % uAddressNearHeapBlock,
        sb0Comment = b"Get heap information",
        bOutputIsInformative = True,
      )
      if not grbIgnoredHeapOutputLines.match(sbLine.strip())
    ];
  if len(asbCdbHeapOutput) == 0:
    return None; # Not part of any heap.
  # Sample output:
  # Allocated memory on "normal" heap
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
  
  assert len(asbCdbHeapOutput) >= 4, \
      "cProcess.fo0GetHeapManagerDataForAddress: Unrecognized !heap output: %s" % repr(asbCdbHeapOutput);
  assert grbHeapOutputFirstLine.match(asbCdbHeapOutput[0]), \
      "Unrecognized page heap report first line:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbHeapOutput);
  obHeapOutputTypeAndRootAddressMatch = grHeapOutputTypeAndRootAddressLine.match(asbCdbHeapOutput[1]);
  assert obHeapOutputTypeAndRootAddressMatch, \
      "Unrecognized page heap report second line:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbHeapOutput);
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
  if u0HeapBlockStartAddress is not None:
    assert u0HeapBlockStartAddress == oHeapManagerData.uHeapBlockStartAddress, \
        "Page heap block start address (@ 0x%X) is different than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.uHeapBlockStartAddress, u0HeapBlockStartAddress);
    assert u0HeapBlockSize == oHeapManagerData.uHeapBlockSize, \
        "Page heap block size (0x%X) is different than reported by cdb (@ 0x%X)" % \
        (oHeapManagerData.uHeapBlockSize, u0HeapBlockSize);
  if gbDebugOutput: print("cProcess.fo0GetHeapManagerDataForAddress: returning %s" % repr(oHeapManagerData));
  return oHeapManagerData;
