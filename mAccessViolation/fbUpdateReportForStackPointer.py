from .fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;
from ..fsGetNumberDescription import fsGetNumberDescription;
from mWindowsAPI import oSystemInfo, cVirtualAllocation;

def fbUpdateReportForStackPointer(
  oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress, sViolationVerb, oVirtualAllocation
):
  oStackVirtualAllocation = cVirtualAllocation(oProcess.uId, oThread.uStackTopAddress - 1);
  assert oStackVirtualAllocation.uEndAddress == oThread.uStackTopAddress, \
      "Memory for the stack should be allocated between 0x%X and 0x%X, but the allocation is from 0x%X to 0x%X" % \
      (oThread.uStackBottomAddress, oThread.uStackTopAddress, oStackVirtualAllocationuStartAddress, oStackVirtualAllocation.uEndAddress);
  # See if the address is near the stack for the current thread:
  uOffsetFromTopOfStack = uAccessViolationAddress - oStackVirtualAllocation.uEndAddress;
  uOffsetFromBottomOfStack = oStackVirtualAllocation.uEndAddress - uAccessViolationAddress;
  if uOffsetFromTopOfStack >= 0 and uOffsetFromTopOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s:Stack+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromTopOfStack));
    oBugReport.sBugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X; %d/0x%X bytes above the top of the stack memory allocation at 0x%X." % \
        (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress, uOffsetFromTopOfStack, uOffsetFromTopOfStack, oStackVirtualAllocation.uEndAddress);
  elif uOffsetFromBottomOfStack >= 0 and uOffsetFromBottomOfStack <= oSystemInfo.uPageSize:
    oBugReport.sBugTypeId = "AV%s:Stack-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromBottomOfStack));
    oBugReport.sBugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X; %d/0x%X bytes below the bottom of the stack memory allocation at 0x%X." % \
        (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress, uOffsetFromBottomOfStack, uOffsetFromBottomOfStack, oStackVirtualAllocation.uStartAddress);
  else:
    return False;
  oBugReport.sSecurityImpact = "Potentially exploitable security issue.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess, oThread, sViolationTypeId)
  );
  return True;
