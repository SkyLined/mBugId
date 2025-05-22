from mWindowsAPI import cVirtualAllocation;

from ...fsGetNumberDescription import fsGetNumberDescription;

def fbUpdateReportForStackPointer(
  oCdbWrapper,
  oBugReport,
  oProcess,
  oThread,
  sViolationTypeId,
  sViolationVerb,
  uAccessViolationAddress,
):
  u0StackTopAddress = oThread.u0StackTopAddress;
  u0StackBottomAddress = oThread.u0StackBottomAddress;
  if u0StackTopAddress is None or u0StackBottomAddress is None:
    return None;
  uStackTopAddress = u0StackTopAddress;
  uStackBottomAddress = u0StackBottomAddress;
  oStackVirtualAllocation = cVirtualAllocation(oProcess.uId, oThread.u0StackTopAddress - 1);
  if (
    oStackVirtualAllocation.uStartAddress > u0StackBottomAddress or
    oStackVirtualAllocation.uEndAddress != uStackTopAddress
  ):
    # This makes little sense, so let's not try to handle it.
    return False;
  # See if the address is near the allocation for the stack for the current thread:
  uOffsetFromTopOfStack = uAccessViolationAddress - oStackVirtualAllocation.uEndAddress;
  uOffsetFromBottomOfStack = oStackVirtualAllocation.uEndAddress - uAccessViolationAddress;
  if uOffsetFromTopOfStack >= 0 and uOffsetFromTopOfStack <= oStackVirtualAllocation.uPageSize:
    oBugReport.s0BugTypeId = "AV%s:Stack+%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromTopOfStack));
    oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X; %d/0x%X bytes above the top of the stack memory allocation at 0x%X." % \
        (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress, uOffsetFromTopOfStack, uOffsetFromTopOfStack, oStackVirtualAllocation.uEndAddress);
  elif uOffsetFromBottomOfStack >= 0 and uOffsetFromBottomOfStack <= oStackVirtualAllocation.uPageSize:
    oBugReport.s0BugTypeId = "AV%s:Stack-%s" % (sViolationTypeId, fsGetNumberDescription(uOffsetFromBottomOfStack));
    oBugReport.s0BugDescription = "An Access Violation exception happened at 0x%X while attempting to %s memory at 0x%X; %d/0x%X bytes below the bottom of the stack memory allocation at 0x%X." % \
        (uAccessViolationAddress, sViolationVerb, uAccessViolationAddress, uOffsetFromBottomOfStack, uOffsetFromBottomOfStack, oStackVirtualAllocation.uStartAddress);
  else:
    return False;
  oBugReport.s0SecurityImpact = "Potentially exploitable security issue.";
  # We assume that there are Guard Pages around the stack, so this exception is
  # never going to be avoidable. This is why we do not set a collateral bug
  # handler here.
  return True;
