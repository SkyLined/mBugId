import re;
from mWindowsAPI import cVirtualAllocation, oSystemInfo;
from mWindowsAPI.mDefines import *;
from dxConfig import dxConfig;

duPoisonValue_by_sISA = {
  "x86": 0x41414141,
  "x64": 0x4141414141414141,
};
  
class cCollateralBugHandler(object):
  def __init__(oSelf, oCdbWrapper, uMaximumNumberOfBugs):
    oSelf.__duPoisonedAddress_by_uProcessId = {};
    oSelf.__uMaximumNumberOfBugs = uMaximumNumberOfBugs;
    oSelf.__uBugCount = 0;
    oSelf.__fbExceptionHandler = None;
    oSelf.uValueIndex = 0;
    oCdbWrapper.fAddEventCallback("Started process", oSelf.fHandleNewProcess);
    oCdbWrapper.fAddEventCallback("Attached to process", oSelf.fHandleNewProcess);
    oCdbWrapper.fAddEventCallback("Process terminated", oSelf.fHandleProcessTerminated);
  
  def fHandleNewProcess(oSelf, oProcess):
    uPoisonAddress = duPoisonValue_by_sISA[oProcess.sISA];
    if uPoisonAddress >= oSystemInfo.uMinimumApplicationAddress and uPoisonAddress < oSystemInfo.uMaximumApplicationAddress:
      # A poisoned pointer can point to allocatable memory, so no need to reserve a region around it to prevent that.
      uVirtualAllocationStartAddress = uPoisonAddress - (uPoisonAddress % oSystemInfo.uAllocationAddressGranularity);
      uVirtualAllocationSize = oSystemInfo.uAllocationAddressGranularity;
      oVirtualAllocation = cVirtualAllocation.foCreateInProcessForId(
        uProcessId = oProcess.uId,
        uAddress = uVirtualAllocationStartAddress,
        uSize = uVirtualAllocationSize,
        bReserved = True,
      );
      uPoisonAddress = oVirtualAllocation.uStartAddress + (uPoisonAddress % oSystemInfo.uAllocationAddressGranularity);
#      print "Reserved 0x%X bytes at 0x%08X around poisoned address 0x%08X" % \
#          (oVirtualAllocation.uSize, oVirtualAllocation.uStartAddress, uPoisonAddress);
#    else:
#      print "Set poison to invalid address 0x%08X" % uPoisonAddress;
    oSelf.__duPoisonedAddress_by_uProcessId[oProcess.uId] = uPoisonAddress;
  
  def fSetExceptionHandler(oSelf, fbExceptionHandler):
    assert oSelf.__fbExceptionHandler is None, \
        "Cannot set two exception handlers!"
    oSelf.__fbExceptionHandler = fbExceptionHandler;
  
  def fbHandleException(oSelf):
    oSelf.__uBugCount += 1;
    if oSelf.__uBugCount >= oSelf.__uMaximumNumberOfBugs or not oSelf.__fbExceptionHandler:
      # Don't handle any more bugs, or don't handle this particular bug.
      return False;
    fbExceptionHandler = oSelf.__fbExceptionHandler;
    oSelf.__fbExceptionHandler = None;
    return fbExceptionHandler(oSelf);
  
  def fHandleProcessTerminated(oSelf, oProcess):
    del oSelf.__duPoisonedAddress_by_uProcessId[oProcess.uId];
  
  def fiGetOffsetForPoisonedAddress(oSelf, oProcess, uAddress):
    uPoisonedAddress = oSelf.__duPoisonedAddress_by_uProcessId[oProcess.uId];
    iOffset = uAddress - uPoisonedAddress;
    # Let's allow a full page of offset on either side.
    if abs(iOffset) >= oSystemInfo.uPageSize:
      # Too far: return None to indicate this is not near the poisoned address.
      return None
    return iOffset
  
  def fuGetPoisonedValue(oSelf, oProcess, uBits, uPointerSizedValue = None):
    auColleteralValues = dxConfig["auColleteralPoisonValues"];
    uPoisonValue = None;
    if oSelf.uValueIndex < len(auColleteralValues):
      uPoisonValue = auColleteralValues[oSelf.uValueIndex];
    if uPoisonValue is None:
      uPoisonValue = uPointerSizedValue is None and duPoisonValue_by_sISA[oProcess.sISA] or uPointerSizedValue;
    oSelf.uValueIndex += 1;
    return uPoisonValue & ((1 << uBits) - 1);
    