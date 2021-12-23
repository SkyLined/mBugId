from mWindowsSDK import *;
from mWindowsAPI import cVirtualAllocation, oSystemInfo;

from ..dxConfig import dxConfig;

def cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW(oBugReport, oProcess, oThread, oException):
  assert oBugReport.o0Stack, \
      "Stack is missing!?";
  oStack = oBugReport.o0Stack;
  # Check if this stack exhaustion happened because it ran out of free memory to to commit more stack space by
  # attempting to allocate some memory in the process.
  try:
    o0TestVirtualAllocation = cVirtualAllocation.fo0CreateForProcessId(oProcess.uId, oSystemInfo.uPageSize);
  except MemoryError:
    oBugReport.s0BugTypeId = "OOM";
    oBugReport.s0BugDescription = "The process was unable to allocate addition stack memory.";
    oBugReport.s0SecurityImpact = "Denial of Service";
    return oBugReport;
  else:
    if o0TestVirtualAllocation:
      o0TestVirtualAllocation.fFree();
  
  # Stack exhaustion can be caused by recursive function calls, where one or more functions repeatedly call themselves
  # Figure out if this is the case and fide all frames at the top of the stack until the "first" frame in the loop.
  oBugReport.s0BugTypeId = "StackExhaustion";
  oBugReport.s0BugDescription = "The process exhausted available stack memory.";
  oBugReport.s0SecurityImpact = "Denial of Service";
  uRecursionStartIndex = None;
  uRecursionLoopSize = None;
  uRecursionLoopCount = None;
  for uFirstLoopStartIndex in range(len(oStack.aoFrames) - 1):
    # Find out how large at most a loop can be and still be repeated often enough for detection in the remaining stack:
    uRemainingStackSize = len(oStack.aoFrames) - uFirstLoopStartIndex;
    uMaxLoopSize = int(uRemainingStackSize / dxConfig["uMinStackRecursionLoops"]);
    for uLoopSize in range(1, min(uMaxLoopSize, dxConfig["uMaxStackRecursionLoopSize"])):
      uLoopCount = 0;
      while uFirstLoopStartIndex + (uLoopCount + 1) * uLoopSize < len(oStack.aoFrames):
        uNthLoopStartIndex = uFirstLoopStartIndex + uLoopCount * uLoopSize;
        for uFrameIndexInLoop in range(uLoopSize):
          oFirstLoopFrameAtIndex = oStack.aoFrames[uFirstLoopStartIndex + uFrameIndexInLoop];
          oNthLoopFrameAtIndex = oStack.aoFrames[uNthLoopStartIndex + uFrameIndexInLoop];
          if oFirstLoopFrameAtIndex.sbAddress != oNthLoopFrameAtIndex.sbAddress:
            break;
        else:
          uLoopCount += 1;
          continue;
        # No more loops
        break;
      if uLoopCount < dxConfig["uMinStackRecursionLoops"]:
        pass;
      elif uRecursionLoopCount is not None and uLoopCount * uLoopSize <= uRecursionLoopCount * uRecursionLoopSize:
        pass;
        # We found enough loops to assume this is a stack recursion issue and this loop includes more frames than
        # any loop we have found so far, so this is a better result.
      else:
        uRecursionStartIndex = uFirstLoopStartIndex;
        uRecursionLoopSize = uLoopSize;
        uRecursionLoopCount = uLoopCount;
  if uRecursionStartIndex is not None:
    # Enough loops were found in the stack to assume this is a recursive function call
    # Obviously a loop has no end and the stack will not be complete so the start of the loop may be unknown. This
    # means there is no obvious way to decide which of the functions involved in the loop is the first or last.
    # In order to create a stack id and to compare two loops, a way to pick a frame as the "first" in the loop
    # is needed that will yield the same results every time. This is currently done by creating a strings
    # concatinating the simplified addresses of all frames in order for each possible "first" frame.
    duStartOffset_by_sbSimplifiedAddresses = {};
    for uStartOffset in range(uRecursionLoopSize):
      sbSimplifiedAddresses = b"".join([
        oStack.aoFrames[uRecursionStartIndex + uStartOffset + uIndex].sb0SimplifiedAddress or b"(unknown)"
        for uIndex in range(0, uRecursionLoopSize)
      ]);
      duStartOffset_by_sbSimplifiedAddresses[sbSimplifiedAddresses] = uStartOffset;
    # These strings are now sorted alphabetically and the first one is picked.
    sbFirstSimplifiedAddresses = sorted(duStartOffset_by_sbSimplifiedAddresses.keys())[0];
    # The associated start offset is added to the start index of the first loop.
    uStartOffset = duStartOffset_by_sbSimplifiedAddresses[sbFirstSimplifiedAddresses];
    uRecursionStartIndex += uStartOffset;
    # Hide all frames at the top of the stack up until the first loop, and mark all frames in the loop as being
    # part of the BugId:
    for oFrame in oStack.aoFrames:
      if oFrame.uIndex < uRecursionStartIndex:
        # All top frames up until the "first" frame in the first loop are hidden:
        oFrame.s0IsHiddenBecause = "This call is not part of the detected recursion loops";
        oFrame.bIsPartOfId = False;
      elif oFrame.uIndex < uRecursionStartIndex + uRecursionLoopSize:
        # All frames in the loop are part of the hash if they have an id:
        # This includes inline frames because they may not get inlined in a different build but the BugId should be
        # the same for both builds.
        oFrame.bIsPartOfId = oFrame.sId is not None;
      else:
        # All frames after the loop are not part of the hash.
        oFrame.bIsPartOfId = False;
    # The bug id and description are adjusted to explain the recursive function call as its cause.
    oBugReport.s0BugTypeId = "RecursiveCall(%d)" % uRecursionLoopSize;
    if uRecursionLoopSize == 1:
      oBugReport.s0BugDescription = "A recursive function call exhausted available stack memory";
    else:
      oBugReport.s0BugDescription = "A recursive function call involving %d functions exhausted available stack memory" % uRecursionLoopSize;
  return oBugReport;
