import re;

class cThreadEnvironmentBlock(object):
  @staticmethod
  def foCreate(oCdbWrapper):
    asPageHeapOutput = oCdbWrapper.fasSendCommandAndReadOutput("!teb", bOutputIsInformative = True);
    if not oCdbWrapper.bCdbRunning: return;
    assert asPageHeapOutput, "Missing TEB info output";
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
    oHeaderMatch = re.match(r"^TEB at ([0-9A-Fa-f]+)$", asPageHeapOutput[0]);
    assert oHeaderMatch, "Unexpected TEB info header:%s\r\n%s" % (asPageHeapOutput[0], "\r\n".join(asPageHeapOutput));
    uTEBAddress = long(oHeaderMatch.group(1), 16);
    uStackTopAddress = None;
    uStackBottomAddress = None;
    for sLine in asPageHeapOutput[1:]:
      oLineMatch = re.match(r"^\s+([\w ]+):\s+([0-9A-Fa-f]+(?: \. [0-9A-Fa-f]+)?)$", sLine);
      assert oLineMatch, "Unexpected TEB info line:%s\r\n%s" % (sLine, "\r\n".join(asPageHeapOutput));
      sName, sValue = oLineMatch.groups();
      if sName == "StackBase":
        uStackTopAddress = long(sValue, 16);
      elif sName == "StackLimit":
        uStackBottomAddress = long(sValue, 16);
    return cThreadEnvironmentBlock(
      uAddress = uTEBAddress,
      uStackTopAddress = uStackTopAddress,
      uStackBottomAddress = uStackBottomAddress,
    );
  
  def __init__(oThreadEnvironmentBlock, uAddress, uStackTopAddress, uStackBottomAddress):
    oThreadEnvironmentBlock.uAddress = uAddress;
    oThreadEnvironmentBlock.uStackTopAddress = uStackTopAddress;
    oThreadEnvironmentBlock.uStackBottomAddress = uStackBottomAddress;
