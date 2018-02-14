from ..cThreadEnvironmentBlock import cThreadEnvironmentBlock;
from fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;
from ..fsGetNumberDescription import fsGetNumberDescription;
from mWindowsAPI import oSystemInfo;

def fbUpdateReportForStackPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  # See if the address is near the stack for the current thread:
  oThreadEnvironmentBlock = cThreadEnvironmentBlock.foCreateForCurrentThread(oProcess);
  uOffsetFromEndOfStack = uAccessViolationAddress - oThreadEnvironmentBlock.uStackAllocationEndAddress;
  uOffsetFromStartOfStack = oThreadEnvironmentBlock.uStackAllocationStartAddress - uAccessViolationAddress;
  if uOffsetFromEndOfStack >= 0 and uOffsetFromEndOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromEndOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes passed the end of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromEndOfStack, uOffsetFromEndOfStack, oThreadEnvironmentBlock.uStackEndAddress);
  elif uOffsetFromStartOfStack >= 0 and uOffsetFromStartOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s[Stack]-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromStartOfStack));
    oBugReport.sBugDescription = "Access violation while %s memory at 0x%X; %d/0x%X bytes before the start of the stack at 0x%X." % \
        (sViolationTypeDescription, uAccessViolationAddress, uOffsetFromStartOfStack, uOffsetFromStartOfStack, oThreadEnvironmentBlock.uStackEndAddress);
  else:
    return False;
  oBugReport.sSecurityImpact = "Potentially exploitable security issue.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
  );
  return True;
