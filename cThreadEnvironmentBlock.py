import re;

class cThreadEnvironmentBlock(object):
  @staticmethod
  def foCreateForCurrentThread(oProcess):
    #TODO: Use NtQueryInformationThread to gather this information.
    asCdbThreadOutput = oProcess.fasExecuteCdbCommand(
      sCommand = "!teb",
      sComment = "Get thread environment info",
      bOutputIsInformative = True,
    );
    assert asCdbThreadOutput, \
        "Missing TEB info output";
    # Sample output:
    # |0:000> !teb
    # |TEB at 00007ff65896e000
    # |    ExceptionList:        0000000000000000
    # |    StackBase:            000000e510bd0000
    # |    StackLimit:           000000e510bcd000
    # |    SubSystemTib:         0000000000000000
    # |    FiberData:            0000000000001e00
    # |    ArbitraryUserPointer: 0000000000000000
    # |    Self:                 00007ff65896e000
    # |    EnvironmentPointer:   0000000000000000
    # |    ClientId:             0000000000001904 . 0000000000001984
    # |    RpcHandle:            0000000000000000
    # |    Tls Storage:          00007ff65896e058
    # |    PEB Address:          00007ff658964000
    # |    LastErrorValue:       0
    # |    LastStatusValue:      c00000bb
    # |    Count Owned Locks:    0
    # |    HardErrorMode:        0
    # Note that the above lines starting with spaces may not be there in cases where there is an error.
    # ---
    # Sometimes this error is output:
    # |error InitTypeRead( TEB32 )...
    # It can show up at any location in the output.
    uTEBAddress = None;
    uStackTopAddress = None;
    uStackBottomAddress = None;
    for sLine in asCdbThreadOutput:
      if sLine == "error InitTypeRead( TEB )...":
        continue; # Ignore this error;
      oHeaderMatch = re.match(r"^(Wow64 )?TEB(32)? at ([0-9A-Fa-f]+)$", sLine);
      if oHeaderMatch:
        if uTEBAddress is not None:
          break; # This is the 64-bit entry that comes after the 32-bit. We only parse the 32-bit one, so stop.
        sWow64, sTEBBits, sTEBAddress = oHeaderMatch.groups();
        uTEBAddress = long(sTEBAddress, 16);
        # Unless it is explicitly mentioned to be a 32-bit TEB, determine TEB pointer size by looking at the length
        # cdb reported the address in: 16 hex digits means 64-bits (8 bytes), 8 hex digits means 32-bits (4 bytes).
        uTEBPointerSize = sTEBBits == "32" or len(sTEBAddress) == 8 and 4 or 8;
      else:
        oLineMatch = re.match(r"^\s+([\w ]+):\s+([0-9A-Fa-f]+(?: \. [0-9A-Fa-f]+)?)$", sLine);
        assert oLineMatch, \
            "Unexpected TEB info line:%s\r\n%s" % (sLine, "\r\n".join(asCdbThreadOutput));
        sName, sValue = oLineMatch.groups();
        if sName == "StackBase":
          uStackTopAddress = long(sValue, 16);
        elif sName == "StackLimit":
          uStackBottomAddress = long(sValue, 16);
    if uStackTopAddress is None:
      # No additional information was provided, we'll have to grab it from the TEB outselves.
      # The TEB has a pointer to the stack top and bottom:
      # http://undocumented.ntinternals.net/index.html?page=UserMode%2FUndocumented%20Functions%2FNT%20Objects%2FThread%2FTEB.html
      # typedef struct _TEB
      # {
      #     struct _NT_TIB                    NtTib;  // size = 7 * pointer
      #     ...snip...
      # struct _NT_TIB {
      #   void *ExceptionList;                        // size = pointer
      #   void *StackBase;                            // size = pointer
      #   void *StackLimit;                           // size = pointer
      #   void *SubSystemTib;                         // size = pointer
      #   union {                                     // size = max(pointer, DWORD)
      #     void *FiberData;                          //    size = pointer
      #     uint32_t Version;                         //    size = DWORD
      #   };                          
      #   void *ArbitraryUserPointer;                 // size = pointer
      #   struct _NT_TIB *Self;                       // size = pointer
      # };                                            // total size =  7 * pointer
      uStackTopAddress = oProcess.fuGetValue(
        "poi(0x%X)" % (uTEBAddress + 1 * uTEBPointerSize),
        "Get stack top address from TEB"
      );
      uStackBottomAddress = oProcess.fuGetValue(
        "poi(0x%X)" % (uTEBAddress + 2 * uTEBPointerSize),
        "Get stack bottom address from TEB"
      );

    return cThreadEnvironmentBlock(
      uAddress = uTEBAddress,
      uStackTopAddress = uStackTopAddress,
      uStackBottomAddress = uStackBottomAddress,
    );
  
  def __init__(oThreadEnvironmentBlock, uAddress, uStackTopAddress, uStackBottomAddress):
    oThreadEnvironmentBlock.uAddress = uAddress;
    oThreadEnvironmentBlock.uStackTopAddress = uStackTopAddress;
    oThreadEnvironmentBlock.uStackBottomAddress = uStackBottomAddress;
