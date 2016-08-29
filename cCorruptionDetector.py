import hashlib;
from dxBugIdConfig import dxBugIdConfig;
from fsGetNumberDescription import fsGetNumberDescription;

class cCorruptionDetector(object):
    # Can be used to check for memory corruption
  def __init__(oCorruptionDetector, oCdbWrapper):
    oCorruptionDetector.oCdbWrapper = oCdbWrapper;
    oCorruptionDetector.dsBytesHex_by_uAddress = {};
    oCorruptionDetector.bCorruptionDetected = False;
    oCorruptionDetector.uCorruptionStartAddress = None;
    oCorruptionDetector.uCorruptionEndAddress = None;
  
  def fDetectCorruption(oCorruptionDetector, uStartAddress, *axExpectedBytes):
    aauExpectedBytes = [isinstance(xExpectedBytes, list) and xExpectedBytes or [xExpectedBytes] for xExpectedBytes in axExpectedBytes];
    uAddress = uStartAddress;
    auBytes = [];
    for auExpectedBytes in aauExpectedBytes:
      uByte = oCorruptionDetector.oCdbWrapper.fuGetValue("by(0x%X)" % uAddress);
      oCorruptionDetector.dsBytesHex_by_uAddress[uAddress] = "%02X" % uByte;
      if uByte not in auExpectedBytes:
        if not oCorruptionDetector.bCorruptionDetected:
          oCorruptionDetector.bCorruptionDetected = True;
          oCorruptionDetector.uCorruptionStartAddress = uAddress;
          oCorruptionDetector.uCorruptionEndAddress = uAddress + 1;
        elif uAddress < oCorruptionDetector.uCorruptionStartAddress:
          oCorruptionDetector.uCorruptionStartAddress = uAddress;
        elif uAddress >= oCorruptionDetector.uCorruptionEndAddress:
          oCorruptionDetector.uCorruptionEndAddress = uAddress + 1;
      uAddress += 1;
  
  def fasCorruptedBytes(oCorruptionDetector):
    uCorruptionLength = oCorruptionDetector.uCorruptionEndAddress - oCorruptionDetector.uCorruptionStartAddress;
    asCorruptedBytes = [];
    for uOffset in xrange(uCorruptionLength):
      uAddress = oCorruptionDetector.uCorruptionStartAddress + uOffset;
      if uAddress not in oCorruptionDetector.dsBytesHex_by_uAddress:
        oCorruptionDetector.dsBytesHex_by_uAddress[uAddress] = \
            "%02X" % oCorruptionDetector.oCdbWrapper.fuGetValue("by(0x%X)" % (uAddress));
      asCorruptedBytes.append(oCorruptionDetector.dsBytesHex_by_uAddress[uAddress]);
    return asCorruptedBytes;
  
  def fsCorruptionId(oCorruptionDetector):
    if dxBugIdConfig["uHeapCorruptedBytesHashChars"] == 0:
      return None;
    oHasher = hashlib.md5();
    oHasher.update("".join(oCorruptionDetector.fasCorruptedBytes()));
    uCorruptionLength = oCorruptionDetector.uCorruptionEndAddress - oCorruptionDetector.uCorruptionStartAddress;
    return "~%s:%s" % (fsGetNumberDescription(uCorruptionLength), \
        oHasher.hexdigest()[:dxBugIdConfig["uHeapCorruptedBytesHashChars"]]);
