import re;
from .dxConfig import dxConfig;
from mWindowsAPI import cVirtualAllocation, oSystemInfo;
from mWindowsSDK import *;

duPoisonValue_by_sISA = {
  "x86": 0x41414141,
  "x64": 0x4141414141414141,
};
  
class cCollateralBugHandler(object):
  def __init__(oSelf, oCdbWrapper, uMaximumNumberOfBugs):
    oSelf.__duPoisonedAddress_by_uProcessId = {};
    oSelf.__uMaximumNumberOfBugs = uMaximumNumberOfBugs;
    oSelf.__uBugCount = 0;
    oSelf.__fbIgnoreException = None;
    oSelf.uValueIndex = 0;
    oCdbWrapper.fAddCallback("Process attached", oSelf.fHandleNewProcess);
    oCdbWrapper.fAddCallback("Process terminated", oSelf.fHandleProcessTerminated);
  
  def fHandleNewProcess(oSelf, oCdbWrapper, oProcess):
    uPoisonAddress = duPoisonValue_by_sISA[oProcess.sISA];
    if uPoisonAddress >= oSystemInfo.uMinimumApplicationAddress and uPoisonAddress < oSystemInfo.uMaximumApplicationAddress:
      # A poisoned pointer can point to allocatable memory, so no need to reserve a region around it to prevent that.
      uVirtualAllocationStartAddress = uPoisonAddress - (uPoisonAddress % oSystemInfo.uAllocationAddressGranularity);
      uVirtualAllocationSize = oSystemInfo.uAllocationAddressGranularity;
      o0VirtualAllocation = cVirtualAllocation.fo0CreateForProcessId(
        uProcessId = oProcess.uId,
        uAddress = uVirtualAllocationStartAddress,
        uSize = uVirtualAllocationSize,
        bReserved = True,
      );
      if not o0VirtualAllocation:
        oCdbWrapper.fLogMessage("Collateral bug handler cannot reserve memory around poison address", {
          "uPoisonAddress": uPoisonAddress, "uProcessId": oProcess.uId, "uSize": uVirtualAllocationSize,
        });
      else:
        uPoisonAddress = o0VirtualAllocation.uStartAddress + (uPoisonAddress % oSystemInfo.uAllocationAddressGranularity);
#      print "Reserved 0x%X bytes at 0x%08X around poisoned address 0x%08X" % \
#          (o0VirtualAllocation.uSize, o0VirtualAllocation.uStartAddress, uPoisonAddress);
#    else:
#      print "Set poison to invalid address 0x%08X" % uPoisonAddress;
    oSelf.__duPoisonedAddress_by_uProcessId[oProcess.uId] = uPoisonAddress;
  
  def fSetIgnoreExceptionFunction(oSelf, fbIgnoreException):
    assert oSelf.__fbIgnoreException is None, \
        "Cannot set two exception handlers!"
    oSelf.__fbIgnoreException = fbIgnoreException;
  
  def fbTryToIgnoreException(oSelf):
    # Try to handle this exception to allow the application to continue in order to find out what collateral bugs
    # we can find.
    oSelf.__uBugCount += 1;
    if oSelf.__uBugCount >= oSelf.__uMaximumNumberOfBugs or not oSelf.__fbIgnoreException:
      # Don't handle any more bugs, or don't handle this particular bug.
      return False;
    fbIgnoreException = oSelf.__fbIgnoreException;
    oSelf.__fbIgnoreException = None;
    return fbIgnoreException(oSelf);
  
  def fDiscardIgnoreExceptionFunction(oSelf):
    # The exception was not considered a bug and the application should handle it; if a handler was set, discard it.
    oSelf.__fbIgnoreException = None;
  
  def fHandleProcessTerminated(oSelf, oCdbWrapper, oProcess):
    del oSelf.__duPoisonedAddress_by_uProcessId[oProcess.uId];
  
  def fiGetOffsetForPoisonedAddress(oSelf, oProcess, uAddress):
    if oProcess.uId not in oSelf.__duPoisonedAddress_by_uProcessId:
      # This is a special case: apparently his bug is in the utility process, which is not in our list.
      # This is highly unexpected, but we need to handle it in order to generate a useful bug report to find out
      # the root cause of this.
      return None;
    uPoisonedAddress = oSelf.__duPoisonedAddress_by_uProcessId[oProcess.uId];
    iOffset = uAddress - uPoisonedAddress;
    # Let's allow a full page of offset on either side.
    if abs(iOffset) >= oSystemInfo.uPageSize:
      # Too far: return None to indicate this is not near the poisoned address.
      return None
    return iOffset
  
  def fuGetPoisonedValue(oSelf, oProcess, uBits, uPointerSizedValue = None):
    auCollateralValues = dxConfig["auCollateralPoisonValues"];
    uPoisonValue = None;
    if oSelf.uValueIndex < len(auCollateralValues):
      uPoisonValue = auCollateralValues[oSelf.uValueIndex];
    if uPoisonValue is None:
      uPoisonValue = uPointerSizedValue is None and duPoisonValue_by_sISA[oProcess.sISA] or uPointerSizedValue;
    oSelf.uValueIndex += 1;
    return uPoisonValue & ((1 << uBits) - 1);
    