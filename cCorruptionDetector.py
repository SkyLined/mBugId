import hashlib;
from dxConfig import dxConfig;
from fsGetNumberDescription import fsGetNumberDescription;

class cCorruptionDetector(object):
    # Can be used to check for memory corruption
  def __init__(oCorruptionDetector, oVirtualAllocation):
    oCorruptionDetector.oVirtualAllocation = oVirtualAllocation;
    oCorruptionDetector.dsCorruptedBytesHex_by_uAddress = {};
    oCorruptionDetector.bCorruptionDetected = False;
    oCorruptionDetector.uCorruptionStartAddress = None; # first corrupted byte as detected by fDetectCorruption
    oCorruptionDetector.uCorruptionSize = None;
    oCorruptionDetector.uCorruptionEndAddress = None; # first non-corrupted byte after corruption
  
  @staticmethod
  def foCreateForHeapAllocation(oHeapAllocation):
    oCorruptionDetector = cCorruptionDetector(oHeapAllocation.oVirtualAllocation);
    oHeapAllocation.fCheckForCorruption(oCorruptionDetector);
    return oCorruptionDetector;
  
  def fbDetectCorruption(oCorruptionDetector, uStartAddress, axExpectedBytes):
    oVirtualAllocation = oCorruptionDetector.oVirtualAllocation;
    uStartOffset = uStartAddress - oVirtualAllocation.uBaseAddress;
    aauExpectedBytes = [isinstance(xExpectedBytes, list) and xExpectedBytes or [xExpectedBytes] for xExpectedBytes in axExpectedBytes];
    auBytes = oVirtualAllocation.fauGetBytesAtOffset(uStartOffset, len(axExpectedBytes));
    for uOffset in xrange(len(axExpectedBytes)):
      uAddress = uStartAddress + uOffset;
      auExpectedBytes = aauExpectedBytes[uOffset];
      uByte = auBytes[uOffset];
      if uByte not in auExpectedBytes:
        oCorruptionDetector.dsCorruptedBytesHex_by_uAddress[uAddress] = uByte is None and "??" or "%02X" % uByte;
        if not oCorruptionDetector.bCorruptionDetected:
          oCorruptionDetector.bCorruptionDetected = True;
          oCorruptionDetector.uCorruptionStartAddress = uAddress;
          oCorruptionDetector.uCorruptionEndAddress = uAddress + 1;
        elif uAddress < oCorruptionDetector.uCorruptionStartAddress:
          oCorruptionDetector.uCorruptionStartAddress = uAddress;
        elif uAddress >= oCorruptionDetector.uCorruptionEndAddress:
          oCorruptionDetector.uCorruptionEndAddress = uAddress + 1;
        oCorruptionDetector.uCorruptionSize = \
            oCorruptionDetector.uCorruptionEndAddress - oCorruptionDetector.uCorruptionStartAddress;
    return oCorruptionDetector.bCorruptionDetected;
  
  def fatxMemoryRemarks(oCorruptionDetector):
    # Coalese corrupted bytes into blocks where possible, then create remarks for each such block or single byte.
    atxMemoryRemarks = [];
    uStartAddress = None;
    uLength = None;
    for uAddress in sorted(oCorruptionDetector.dsCorruptedBytesHex_by_uAddress.keys()):
      if uStartAddress is None or uAddress != uStartAddress + uLength:
        if uStartAddress is not None:
          atxMemoryRemarks.append(("Corrupted", uStartAddress, uLength));
        uStartAddress = uAddress;
        uLength = 1;
      else:
        uLength += 1;
    if uStartAddress is not None:
      atxMemoryRemarks.append(("Corrupted", uStartAddress, uLength));
    return atxMemoryRemarks;
  
  def fasCorruptedBytes(oCorruptionDetector):
    # xrange can't handle longs, so we have to work around that:
    uStartAddress = oCorruptionDetector.uCorruptionStartAddress;
    uLength = oCorruptionDetector.uCorruptionEndAddress - uStartAddress;
    return [
      oCorruptionDetector.dsCorruptedBytesHex_by_uAddress.get(uStartAddress + uOffset, "??")
      for uOffset in xrange(uLength)
    ];
  
  def fsCorruptionId(oCorruptionDetector):
    uCorruptionLength = oCorruptionDetector.uCorruptionEndAddress - oCorruptionDetector.uCorruptionStartAddress;
    sId = "~%s" % fsGetNumberDescription(uCorruptionLength);
    if dxConfig["uHeapCorruptedBytesHashChars"]:
      oHasher = hashlib.md5();
      oHasher.update("".join(oCorruptionDetector.fasCorruptedBytes()));
      sId += "#%s" % oHasher.hexdigest()[:dxConfig["uHeapCorruptedBytesHashChars"]];
    return sId;
