from ..cThreadEnvironmentBlock import cThreadEnvironmentBlock;
from fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;
from ..fsGetNumberDescription import fsGetNumberDescription;
from mWindowsAPI import oSystemInfo;

def fbUpdateReportForStackPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  # See if the address is near the stack for the current thread:
  oThreadEnvironmentBlock = cThreadEnvironmentBlock.foCreateForCurrentThread(oProcess);
  uOffsetFromTopOfStack = uAccessViolationAddress - oThreadEnvironmentBlock.uStackTopAddress;
  uOffsetFromBottomOfStack = oThreadEnvironmentBlock.uStackBottomAddress - uAccessViolationAddress;
  if uOffsetFromTopOfStack >= 0 and uOffsetFromTopOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromTopOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes passed the top of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromTopOfStack, uOffsetFromTopOfStack, oThreadEnvironmentBlock.uStackTopAddress);
  elif uOffsetFromBottomOfStack >= 0 and uOffsetFromBottomOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromBottomOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes before the bottom of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromBottomOfStack, uOffsetFromBottomOfStack, oThreadEnvironmentBlock.uStackTopAddress);
  else:
    return False;
  oBugReport.sSecurityImpact = "Potentially exploitable security issue.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;
