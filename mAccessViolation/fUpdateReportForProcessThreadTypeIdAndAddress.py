from .fbUpdateReportForAllocatedPointer import fbUpdateReportForAllocatedPointer;
from .fbUpdateReportForCollateralPoisonPointer import fbUpdateReportForCollateralPoisonPointer;
from .fbUpdateReportForUnallocatedPointer import fbUpdateReportForUnallocatedPointer;
from .fbUpdateReportForHeapManagerPointer import fbUpdateReportForHeapManagerPointer;
from .fbUpdateReportForInvalidPointer import fbUpdateReportForInvalidPointer;
from .fbUpdateReportForNULLPointer import fbUpdateReportForNULLPointer;
from .fbUpdateReportForReservedPointer import fbUpdateReportForReservedPointer;
from .fbUpdateReportForSpecialPointer import fbUpdateReportForSpecialPointer;
from .fbUpdateReportForStackPointer import fbUpdateReportForStackPointer;
from mWindowsAPI import cVirtualAllocation;

def fUpdateReportForProcessThreadTypeIdAndAddress(oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress):
  
  sViolationTypeDescription = {"R":"reading", "W":"writing", "E":"executing"}.get(sViolationTypeId, "accessing");
  oVirtualAllocation = cVirtualAllocation(oProcess.uId, uAccessViolationAddress);
  
  # Handling this AV as the appropriate type of pointer:
  for fbUpdateReportForSpecificPointerType in [
    fbUpdateReportForNULLPointer,
    fbUpdateReportForCollateralPoisonPointer,
    fbUpdateReportForHeapManagerPointer,
    fbUpdateReportForStackPointer,
    fbUpdateReportForSpecialPointer,
    fbUpdateReportForAllocatedPointer,
    fbUpdateReportForReservedPointer,
    fbUpdateReportForUnallocatedPointer,
    fbUpdateReportForInvalidPointer,
  ]:
    if fbUpdateReportForSpecificPointerType(
      oCdbWrapper, oBugReport, oProcess, oThread, sViolationTypeId, uAccessViolationAddress,
      sViolationTypeDescription, oVirtualAllocation
    ):
      # We handled the pointer as this type, and it can be only one type, so stop trying other types:
      return;
  else:
    # This pointer is not of a known type: should never happend
    raise AssertionError("Could not handle AV%s@0x%08X" % (sViolationTypeId, uAccessViolationAddress));
