import re;

from mWindowsAPI import cVirtualAllocation, oSystemInfo;

from ..dxConfig import dxConfig;

from .cCollateralBugHandler_fbIgnoreAccessViolationException import \
    cCollateralBugHandler_fbIgnoreAccessViolationException;
from .cCollateralBugHandler_fbPoisonFlags import cCollateralBugHandler_fbPoisonFlags;
from .cCollateralBugHandler_fbPoisonRegister import cCollateralBugHandler_fbPoisonRegister;

duPoisonValue_by_sISA = {
  "x86": 0x41414141,
  "x64": 0x4141414141414141,
};
  
class cCollateralBugHandler(object):
  def __init__(oSelf, oCdbWrapper, u0MaximumNumberOfBugs, f0iInteractiveAskForValue):
    oSelf.__oCdbWrapper = oCdbWrapper;
    oSelf.__duPoisonedAddress_by_uProcessId = {};
    oSelf.__u0MaximumNumberOfBugs = u0MaximumNumberOfBugs;
    oSelf.__f0iInteractiveAskForValue = f0iInteractiveAskForValue;
    oSelf.__uBugCount = 0;
    oSelf.__f0bIgnoreException = None;
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
    assert oSelf.__f0bIgnoreException is None, \
        "Cannot set two exception handlers!"
    oSelf.__f0bIgnoreException = fbIgnoreException;
  
  def fbTryToIgnoreException(oSelf):
    # Try to handle this exception to allow the application to continue in order to find out what collateral bugs
    # we can find.
    oSelf.__uBugCount += 1;
    bMaximumNumberOfBugsReached = oSelf.__u0MaximumNumberOfBugs is not None and oSelf.__uBugCount >= oSelf.__u0MaximumNumberOfBugs;
    if bMaximumNumberOfBugsReached or not oSelf.__f0bIgnoreException:
      # Don't handle any more bugs, or don't handle this particular bug.
      sMessage = "The %s." % " and the ".join(s for s in [
        "last detected bug cannot currently be ignored" if oSelf.__f0bIgnoreException is None else None,
        "maximum number of bugs has been reached" if bMaximumNumberOfBugsReached else None,
      ] if s);
      oSelf.__oCdbWrapper.fLogMessage(sMessage);
      oSelf.__oCdbWrapper.fFireCallbacks("Bug cannot be ignored", sMessage);
      return False;
    fbIgnoreException = oSelf.__f0bIgnoreException;
    oSelf.__f0bIgnoreException = None;
    return fbIgnoreException(oSelf);
  
  def fDiscardIgnoreExceptionFunction(oSelf):
    # The exception was not considered a bug and the application should handle it; if a handler was set, discard it.
    oSelf.__f0bIgnoreException = None;
  
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
  
  def fuGetPoisonedValue(oSelf, oProcess, oWindowsAPIThread, sDestination, sInstruction, i0CurrentValue, uBits, u0PointerSizedOriginalValue):
    auCollateralValues = dxConfig["auCollateralPoisonValues"];
    if oSelf.uValueIndex < len(auCollateralValues):
      uPoisonValue = auCollateralValues[oSelf.uValueIndex];
    else:
      uPoisonValue = duPoisonValue_by_sISA[oProcess.sISA];
    oSelf.uValueIndex += 1;
    uPoisonValue = uPoisonValue & ((1 << uBits) - 1);
    if not oSelf.__f0iInteractiveAskForValue:
      return uPoisonValue;
    while 1:
      iMinValue = -(1 << (uBits - 1));
      uMaxValue = (1 << uBits) - 1;
      u0OriginalValue = None if u0PointerSizedOriginalValue is None else (u0PointerSizedOriginalValue & uMaxValue);
      a0txRegisters = oProcess.fa0txGetRegistersForThreadId(oWindowsAPIThread.uId);
      iUserProvidedValue = oSelf.__f0iInteractiveAskForValue(
        uProcessId = oProcess.uId,
        uThreadId = oWindowsAPIThread.uId,
        sInstruction = sInstruction,
        a0txRegisters = a0txRegisters,
        sDestination = sDestination,
        i0CurrentValue = i0CurrentValue,
        u0OriginalValue = u0OriginalValue,
        iMinValue = iMinValue,
        iMaxValue = uMaxValue,
        iSuggestedValue = uPoisonValue,
      );
      assert iMinValue <= iUserProvidedValue <= uMaxValue, \
          "Value %s0x%X, returned by f0iInteractiveAskForValue (%s) is not in range -0x%X - 0x%X" % (
            "-" if iUserProvidedValue < 0 else "", abs(iUserProvidedValue),
            repr(oSelf.__f0iInteractiveAskForValue),
            abs(iMinValue),
            uMaxValue,
          );
      return iUserProvidedValue & uMaxValue;

  fbIgnoreAccessViolationException = cCollateralBugHandler_fbIgnoreAccessViolationException;
  fbPoisonFlags = cCollateralBugHandler_fbPoisonFlags;
  fbPoisonRegister = cCollateralBugHandler_fbPoisonRegister;
