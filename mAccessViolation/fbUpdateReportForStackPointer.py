from .fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;
from ..fsGetNumberDescription import fsGetNumberDescription;
from mWindowsAPI import oSystemInfo;

def fbUpdateReportForStackPointer(
  oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  # See if the address is near the stack for the current thread:
  uOffsetFromTopOfStack = uAccessViolationAddress - oThread.uStackTopAddress;
  uOffsetFromBottomOfStack = oThread.uStackBottomAddress - uAccessViolationAddress;
  if uOffsetFromTopOfStack >= 0 and uOffsetFromTopOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromTopOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes above the top of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromTopOfStack, uOffsetFromTopOfStack, oThread.uStackTopAddress);
  elif uOffsetFromBottomOfStack >= 0 and uOffsetFromBottomOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromBottomOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes below the bottom of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromBottomOfStack, uOffsetFromBottomOfStack, oThread.uStackBottomAddress);
  else:
    return False;
  oBugReport.sSecurityImpact = "Potentially exploitable security issue.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess, oThread, sViolationTypeId)
  );
  return True;
