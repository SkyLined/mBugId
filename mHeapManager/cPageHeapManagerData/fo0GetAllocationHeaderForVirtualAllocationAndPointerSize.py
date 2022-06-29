from mWindowsAPI import fsHexNumber;

from .mPageHeapStructuresAndStaticValues import \
  DPH_ALLOCATION_HEADER32, DPH_ALLOCATION_HEADER64, \
  auValidPageHeapAllocationHeaderMarkers;

def fo0GetAllocationHeaderForVirtualAllocationAndPointerSize(oHeapBlockVirtualAllocation, uPointerSize, bDebugOutput):
  assert oHeapBlockVirtualAllocation.bAllocated, \
      "Please check oHeapBlockVirtualAllocation.bAllocated == True before making this call\r\n%s" % \
      str(oHeapBlockVirtualAllocation);
  # A page heap allocation for a heap block starts with a DPH_ALLOCATION_HEADER structure:
  DPH_ALLOCATION_HEADER = {4: DPH_ALLOCATION_HEADER32, 8: DPH_ALLOCATION_HEADER64}[uPointerSize];
  oAllocationHeader = oHeapBlockVirtualAllocation.foReadStructureForOffset(
    cStructure = DPH_ALLOCATION_HEADER,
    uOffset = 0,
  );
  if not oAllocationHeader.uMarker in auValidPageHeapAllocationHeaderMarkers:
    if bDebugOutput:
      print("cPageHeapManagerData: Allocation Header marker %s not valid in %s => None\r\n%s" %  (
        fsHexNumber(oAllocationHeader.uMarker.fuGetValue()),
        oHeapBlockVirtualAllocation,
        "\r\n".join(oAllocationHeader.fasDump()),
      ));
    return None;
# Maybe this should be enabled in a "strict" setting, as I would like to know what other values are common. But I've
# missed bugs because this assertion terminated cBugId while reporting one, which is not good.
#    if hasattr(oAllocationHeader, "uPadding"):
#      assert oAllocationHeader.uPadding in auValidPageHeapAllocationHeaderPaddings, \
#          "Page heap allocation header padding has unhandled value 0x%X (expected %s):\r\n%s" % \
#          (oAllocationHeader.uPadding, " or ".join(["0x%X" % uValidMarker for uValidMarker in auValidPageHeapAllocationHeaderPaddings]),
#          "\r\n".join(oAllocationHeader.fasDump()));
  if bDebugOutput:
    print(("┌─ oAllocationHeader ").ljust(80, "─"));
    for sLine in oAllocationHeader.fasDump():
      print("│ %s" % sLine);
    print("└".ljust(80, "─"));
  return oAllocationHeader;
