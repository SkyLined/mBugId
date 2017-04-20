import re;

PAGE_NOACCESS           =       0x1;
PAGE_READONLY           =       0x2;
PAGE_READWRITE          =       0x4;
PAGE_WRITECOPY          =       0x8;
PAGE_EXECUTE            =      0x10;
PAGE_EXECUTE_READ       =      0x20;
PAGE_EXECUTE_READWRITE  =      0x40;
PAGE_EXECUTE_WRITECOPY  =      0x80;
MEM_COMMIT              =    0x1000;
MEM_RESERVE             =    0x2000;
MEM_FREE                =   0x10000;
MEM_PRIVATE             =   0x20000;
MEM_MAPPED              =   0x40000;
MEM_IMAGE               = 0x1000000;


class cVirtualAllocation(object):
  @staticmethod
  def foGetForAddress(oCdbWrapper, uAddress):
    asVProtOutput = oCdbWrapper.fasSendCommandAndReadOutput(
      "!vprot 0x%X; $$ Get memory protection information" % uAddress,
      bOutputIsInformative = True,
    );
    if not oCdbWrapper.bCdbRunning: return None;
    # BaseAddress:       00007df5ff5f0000
    # AllocationBase:    00007df5ff5f0000
    # AllocationProtect: 00000001  PAGE_NOACCESS
    # RegionSize:        0000000001d34000
    # State:             00002000  MEM_RESERVE
    # Type:              00040000  MEM_MAPPED
    
    # BaseAddress:       0000000000000000
    # AllocationBase:    0000000000000000
    # RegionSize:        0000000022f60000
    # State:             00010000  MEM_FREE
    # Protect:           00000001  PAGE_NOACCESS
    
    # BaseAddress:       00007ffffffe0000
    # AllocationBase:    00007ffffffe0000
    # AllocationProtect: 00000002  PAGE_READONLY
    # RegionSize:        0000000000010000
    # State:             00002000  MEM_RESERVE
    # Protect:           00000001  PAGE_NOACCESS
    # Type:              00020000  MEM_PRIVATE
    
    # !vprot: extension exception 0x80004002
    #     "QueryVirtual failed"
    assert len(asVProtOutput) > 0, \
        "!vprot did not return any results.";
    if asVProtOutput[0] in [
      # This happens on x64 when the address is outside of the legal range for userland addresses (>= 0x7fffffff0000)
      "ERROR: !vprot: extension exception 0x80004002.",
      # Not sure when this happens, but handling it as if no memory is allocated in the area.
      "!vprot: No containing memory region found",
    ]:
      return None;
    uBaseAddress = None;
    uAllocationBaseAddress = None;
    uInitialProtection = None;
    uSize = None;
    uState = None;
    uProtection = None;
    uType = None;
    for sLine in asVProtOutput:
      oLineMatch = re.match(r"^(\w+):\s+([0-9a-f]+)(?:\s+\w+)?$", sLine);
      assert oLineMatch, \
          "Unrecognized !vprot output line: %s\r\n%s" % (sLine, "\r\n".join(asVProtOutput));
      sInfoType, sValue = oLineMatch.groups();
      uValue = long(sValue, 16);
      if sInfoType == "BaseAddress":
        uBaseAddress = uValue;
      elif sInfoType == "AllocationBase":
        uAllocationBaseAddress = uValue;
      elif sInfoType == "AllocationProtect":
        uInitialProtection = uValue;
      elif sInfoType == "RegionSize":
        uSize = uValue;
      elif sInfoType == "State":
        uState = uValue;
      elif sInfoType == "Protect":
        uProtection = uValue;
      elif sInfoType == "Type":
        uType = uValue;
    return cVirtualAllocation(
      oCdbWrapper = oCdbWrapper,
      oProcess = oCdbWrapper.oCurrentProcess,
      uBaseAddress = uBaseAddress,
      uAllocationBaseAddress = uAllocationBaseAddress,
      uInitialProtection = uInitialProtection,
      uSize = uSize,
      uState = uState,
      uProtection = uProtection,
      uType = uType,
    );
  
  def __init__(oVirtualAllocation, oCdbWrapper, oProcess, uBaseAddress, uAllocationBaseAddress, uInitialProtection, uSize, uState, uProtection, uType):
    oVirtualAllocation.oCdbWrapper = oCdbWrapper;
    oVirtualAllocation.oProcess = oProcess;
    oVirtualAllocation.uBaseAddress = uBaseAddress;
    oVirtualAllocation.uAllocationBaseAddress = uAllocationBaseAddress;
    oVirtualAllocation.uInitialProtection = uInitialProtection;
    oVirtualAllocation.uSize = uSize;
    oVirtualAllocation.uState = uState;
    oVirtualAllocation.uProtection = uProtection;
    oVirtualAllocation.uType = uType;
    # Convenience:
    oVirtualAllocation.uEndAddress = uBaseAddress + uSize;
    # State:
    oVirtualAllocation.bAllocated = uState == MEM_COMMIT;
    oVirtualAllocation.bReserved = uState == MEM_RESERVE;
    oVirtualAllocation.bUnallocated = uState == MEM_FREE;
    # Type:
    oVirtualAllocation.bMappedImage = uType == MEM_IMAGE;
    oVirtualAllocation.bMappedSection = uType == MEM_MAPPED;
    oVirtualAllocation.bPrivate = uType == MEM_PRIVATE;
    # Protection:
    oVirtualAllocation.__fUpdateProtectionConvenience();
    oVirtualAllocation.__auBytes = None;

  def __fUpdateProtectionConvenience(oVirtualAllocation):
    oVirtualAllocation.bAccessible = oVirtualAllocation.uProtection in [
                          PAGE_READONLY,        PAGE_READWRITE,         PAGE_WRITECOPY,
      PAGE_EXECUTE,       PAGE_EXECUTE_READ,    PAGE_EXECUTE_READWRITE, PAGE_EXECUTE_WRITECOPY
    ];
    oVirtualAllocation.bReadable = oVirtualAllocation.uProtection in [
                          PAGE_READONLY,        PAGE_READWRITE,         PAGE_WRITECOPY,
                          PAGE_EXECUTE_READ,    PAGE_EXECUTE_READWRITE, PAGE_EXECUTE_WRITECOPY
    ];
    oVirtualAllocation.bWritable = oVirtualAllocation.uProtection in [
                                                PAGE_READWRITE,         PAGE_WRITECOPY,
                                                PAGE_EXECUTE_READWRITE, PAGE_EXECUTE_WRITECOPY
    ];
    oVirtualAllocation.bWriteCopy = oVirtualAllocation.uProtection in [
                                                                        PAGE_WRITECOPY,
                                                                        PAGE_EXECUTE_WRITECOPY
    ];
    oVirtualAllocation.bExecutable = oVirtualAllocation.uProtection in [
      PAGE_EXECUTE,       PAGE_EXECUTE_READ,    PAGE_EXECUTE_READWRITE, PAGE_EXECUTE_WRITECOPY
    ];
  
  @staticmethod
  def fsProtection(uProtection):
    return {
      PAGE_NOACCESS: "PAGE_NOACCESS",
      PAGE_READONLY: "PAGE_READONLY",
      PAGE_READWRITE: "PAGE_READWRITE",
      PAGE_WRITECOPY: "PAGE_WRITECOPY",
      PAGE_EXECUTE: "PAGE_EXECUTE",
      PAGE_EXECUTE_READ: "PAGE_EXECUTE_READ",
      PAGE_EXECUTE_READWRITE: "PAGE_EXECUTE_READWRITE",
      PAGE_EXECUTE_WRITECOPY: "PAGE_EXECUTE_WRITECOPY",
    }.get(uProtection);
  
  def fbSetProtection(oVirtualAllocation, uProtection):
    oCdbWrapper = oVirtualAllocation.oCdbWrapper;
    if not oCdbWrapper.oExtension:
      return False;
    assert fsProtection(uProtection), \
        "Invalid protection 0x%X" % uProtection;
    uOldProtection = oCdbWrapper.oExtension.fuSetMemoryProtection(
      oVirtualAllocation.uBaseAddress,
      oVirtualAllocation.uSize,
      oVirtualAllocation.uProtection
    );
    assert uOldProtection == oVirtualAllocation.uProtection, \
      "Expected old memory protection to be 0x%X, but got 0x%X" % (oVirtualAllocation.uProtection, uOldProtection);
    # Update internal value
    oVirtualAllocation.uProtection = uProtection;
    oVirtualAllocation.__fUpdateProtectionConvenience();
    return True;
  
  def fauGetBytesAtOffset(oVirtualAllocation, uOffset = 0, uSize = None):
    oCdbWrapper = oVirtualAllocation.oCdbWrapper;
    if not oVirtualAllocation.bAllocated:
      return None;
    if uSize is None:
      uSize = oVirtualAllocation.uSize - uOffset;
    assert uOffset + uSize <= oVirtualAllocation.uSize, \
        "Cannot get 0x%X bytes at offset 0x%X from a 0x%X byte allocation!" % (uSize, uOffset, oVirtualAllocation.uSize);
    if oVirtualAllocation.__auBytes is None:
      if not oVirtualAllocation.bReadable:
        # Make the memory readable if it is not
        uOriginalProtection = oVirtualAllocation.uProtection;
        oCdbWrapper.oExtension.fuSetVirtualAllocationProtection(
          oVirtualAllocation.uBaseAddress, oVirtualAllocation.uSize, PAGE_READONLY,
          "Marking virtual allocation readable to extract contents",
        );
      else:
        uOriginalProtection = None;
      oVirtualAllocation.__auBytes = oCdbWrapper.fauGetBytes(
        oVirtualAllocation.uBaseAddress, oVirtualAllocation.uSize, "Get virtual allocation content",
      );
      if uOriginalProtection is not None:
        # Restore the original memory protection if it was changed.
        oCdbWrapper.oExtension.fuSetVirtualAllocationProtection(
          oVirtualAllocation.uBaseAddress, oVirtualAllocation.uSize, uOriginalProtection,
          "Restoring virtual allocation protection after extracting contents",
        );
    return oVirtualAllocation.__auBytes[uOffset:uOffset + uSize];
  
  def fuGetValueAtOffset(oVirtualAllocation, uOffset, uSize):
    oCdbWrapper = oVirtualAllocation.oCdbWrapper;
    auBytes = oVirtualAllocation.fauGetBytesAtOffset(uOffset, uSize);
    if auBytes is None:
      return None;
    uValue = 0;
    while auBytes: # little endian
      uValue = (uValue << 8) + auBytes.pop();
    return uValue;
