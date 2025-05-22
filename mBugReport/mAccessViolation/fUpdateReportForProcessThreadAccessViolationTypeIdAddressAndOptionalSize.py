from mWindowsAPI import cVirtualAllocation;

from .fbUpdateReportForAllocatedPointer import fbUpdateReportForAllocatedPointer;
from .fbUpdateReportForCollateralPoisonPointer import fbUpdateReportForCollateralPoisonPointer;
from .fbUpdateReportForGuardPagePointer import fbUpdateReportForGuardPagePointer;
from .fbUpdateReportForHeapManagerPointer import fbUpdateReportForHeapManagerPointer;
from .fbUpdateReportForInvalidPointer import fbUpdateReportForInvalidPointer;
from .fbUpdateReportForNULLPointer import fbUpdateReportForNULLPointer;
from .fbUpdateReportForReservedPointer import fbUpdateReportForReservedPointer;
from .fbUpdateReportForSpecialPointer import fbUpdateReportForSpecialPointer;
from .fbUpdateReportForStackPointer import fbUpdateReportForStackPointer;
from .fbUpdateReportForUnallocatedPointer import fbUpdateReportForUnallocatedPointer;

# Set to true to debug cases where we cannot handle an access violation.
# No such cases are currently known.
gbAssertOnInabilityToHandleAccessViolation = True;

def fUpdateReportForProcessThreadAccessViolationTypeIdAddressAndOptionalSize(
  oCdbWrapper: object,
  oBugReport: object,
  oProcess: object,
  oThread: object,
  sViolationTypeId: str,
  uAccessViolationAddress: int,
  u0AccessViolationSize: int | None = None,
):
  oBugReport.s0BugTypeId = f"AV{sViolationTypeId}";
  sViolationVerb = {"R":"read", "W":"write", "E":"execute", "?": "access"}[sViolationTypeId];
  # Access violations can happen with certain special pointer values and types
  # which we handle here first:
  for fbUpdateReportForSpecificPointerType in [
    fbUpdateReportForNULLPointer,
    fbUpdateReportForCollateralPoisonPointer,
    fbUpdateReportForHeapManagerPointer,
    fbUpdateReportForSpecialPointer,
    fbUpdateReportForStackPointer,
  ]:
    if fbUpdateReportForSpecificPointerType(
      oCdbWrapper,
      oBugReport,
      oProcess,
      oThread,
      sViolationTypeId,
      sViolationVerb,
      uAccessViolationAddress,
    ):
      return;
  
  # Access violations can happen because there is no virtual allocation, or a
  # virtual allocation doesn't allow this access, or when memory is being
  # access at an invalid address.
  # The instruction may have attempt to access multiple bytes of memory, so
  # this access may span 0, 1 or 2 virtual allocations.
  # We will first check if the access violation is caused by the (lack of a)
  # virtual allocation at the start of the access:
  oStartVirtualAllocation = cVirtualAllocation(oProcess.uId, uAccessViolationAddress);
  for fbUpdateReportForSpecificPointerType in [
    fbUpdateReportForUnallocatedPointer,
    fbUpdateReportForReservedPointer,
    fbUpdateReportForGuardPagePointer,
    fbUpdateReportForInvalidPointer,
    fbUpdateReportForAllocatedPointer,
  ]:
    if fbUpdateReportForSpecificPointerType(
      oCdbWrapper,
      oBugReport,
      oProcess,
      oThread,
      sViolationTypeId,
      sViolationVerb,
      uAccessViolationAddress,
      oStartVirtualAllocation,
    ):
      return;
  # It does  appear that the was a virtual allocation at the start address but
  # it could have caused the AV; let's try and guess where the access may have
  # ended, then check if that is outside of the virtual allocation we just
  # checked. If so, we need to check the next virtual allocation:
  if u0AccessViolationSize is not None:
    uAssumedAccessViolationEndAddress = uAccessViolationAddress + u0AccessViolationSize;
  else:
    # Registers can be up to 512 bit (e.g. zmm) so let's assume that's the
    # farthest the access could have reached:
    uAssumedAccessViolationEndAddress = uAccessViolationAddress + 64;
  if uAssumedAccessViolationEndAddress > oStartVirtualAllocation.uEndAddress:
    # In this case, the access violation would have triggered as soon as bytes
    # were accessed immediately after the virtual allocation we just checked.
    # So let's found out what virtual allocation comes after (if any) and check
    # if that could have caused it:
    uAssumedAccessViolationAddress = oStartVirtualAllocation.uEndAddress;
    oEndVirtualAllocation = cVirtualAllocation(oProcess.uId, uAssumedAccessViolationAddress);
    for fbUpdateReportForSpecificPointerType in [
      fbUpdateReportForUnallocatedPointer,
      fbUpdateReportForReservedPointer,
      fbUpdateReportForGuardPagePointer,
      fbUpdateReportForInvalidPointer,
      fbUpdateReportForAllocatedPointer,
    ]:
      if fbUpdateReportForSpecificPointerType(
        oCdbWrapper,
        oBugReport,
        oProcess,
        oThread,
        sViolationTypeId,
        sViolationVerb,
        oEndVirtualAllocation.uStartAddress,
        oEndVirtualAllocation,
      ):
        return;
      print("✘ not %s" % repr(fbUpdateReportForSpecificPointerType));
  # We cannot figure out what caused this access violation.
  if gbAssertOnInabilityToHandleAccessViolation:
    print("oProcess.uId: 0x%X" % oProcess.uId);
    print("sViolationTypeId: %s" % sViolationTypeId);
    print("uAccessViolationAddress: 0x%X" % uAccessViolationAddress);
    print("u0AccessViolationSize: %s" % ("None" if u0AccessViolationSize is None else "0x%X" % u0AccessViolationSize));
    print("oStartVirtualAllocation: %s" % repr(oStartVirtualAllocation));
    try:
      print("oEndVirtualAllocation: %s" % repr(oEndVirtualAllocation));
    except UnboundLocalError:
      print("oEndVirtualAllocation: <not created>");
    raise NotImplemented("Could not handle AV%s@0x%08X" % (sViolationTypeId, uAccessViolationAddress));
  return;
