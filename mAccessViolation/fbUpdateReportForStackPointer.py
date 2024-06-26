from ..fsGetNumberDescription import fsGetNumberDescription;
from mWindowsAPI import oSystemInfo, cVirtualAllocation;

def fbUpdateReportForStackPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  uAccessViolationAddress,
  sViolationVerb,
):
  u0StackTopAddress = oThread.u0StackTopAddress;
  u0StackBottomAddress = oThread.u0StackBottomAddress;
  if u0StackTopAddress is None or u0StackBottomAddress is None:
    return None;
  uStackTopAddress = u0StackTopAddress;
  uStackBottomAddress = u0StackBottomAddress;
  oStackVirtualAllocation = cVirtualAllocation(oProcess.uId, oThread.u0StackTopAddress - 1);
  assert oStackVirtualAllocation.uEndAddress == uStackTopAddress, \
      "Memory for the stack should be allocated between 0x%X and 0x%X, but the allocation is from 0x%X to 0x%X" % \
      (uStackBottomAddress, uStackTopAddress, oStackVirtualAllocation.uStartAddress, oStackVirtualAllocation.uEndAddress);
  # See if the address is near the stack for the current thread:
  uOffsetFromTopOfStack = uAccessViolationAddress - oStackVirtualAllocation.uEndAddress;
  uOffsetFromBottomOfStack = oStackVirtualAllocation.uEndAddress - uAccessViolationAddress;
  if uOffsetFromTopOfStack >= 0 and uOffsetFromTopOfStack <= oSystemInfo.uPageSize:
    oBugReport.s0BugTypeId = "AV%s:Stack+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromTopOfStack));
    oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X; %d/0x%X bytes above the top of the stack memory allocation at 0x%X." % \
        (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress, uOffsetFromTopOfStack, uOffsetFromTopOfStack, oStackVirtualAllocation.uEndAddress);
  elif uOffsetFromBottomOfStack >= 0 and uOffsetFromBottomOfStack <= oSystemInfo.uPageSize:
    oBugReport.s0BugTypeId = "AV%s:Stack-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromBottomOfStack));
    oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X; %d/0x%X bytes below the bottom of the stack memory allocation at 0x%X." % \
        (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress, uOffsetFromBottomOfStack, uOffsetFromBottomOfStack, oStackVirtualAllocation.uStartAddress);
  else:
    return False;
  oBugReport.s0SecurityImpact = "Potentially exploitable security issue.";
  oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
    oCollateralBugHandler.fbIgnoreAccessViolationException(
      oCdbWrapper, oProcess, oThread, sViolationTypeId, uAccessViolationAddress
    )
  );
  return True;
