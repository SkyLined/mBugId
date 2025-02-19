from mWindowsAPI import cVirtualAllocation, oSystemInfo;

from ..dxConfig import dxConfig;

gbDebugOutput = False;

def cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW(oBugReport, oProcess, oWindowsAPIThread, oException):
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
        if gbDebugOutput: print ("Ignored %d loops of size %d at %d: not enough loops (min: %d)" % (
          uLoopCount,
          uLoopSize,
          uFirstLoopStartIndex,
          dxConfig["uMinStackRecursionLoops"]
        ));
        pass;
      elif uRecursionLoopCount is not None and uLoopCount * uLoopSize <= uRecursionLoopCount * uRecursionLoopSize:
        if gbDebugOutput: print ("Ignored %d loops of size %d at %d: less frames (%d) than previously found loop" % (
          uLoopCount,
          uLoopSize,
          uFirstLoopStartIndex,
          uLoopCount * uLoopSize
        ));
        pass;
        # We found enough loops to assume this is a stack recursion issue and this loop includes more frames than
        # any loop we have found so far, so this is a better result.
      else:
        if gbDebugOutput: print ("Found %d loops of size %d at %d." % (
          uLoopCount,
          uLoopSize,
          uFirstLoopStartIndex,
        ));
        uRecursionStartIndex = uFirstLoopStartIndex;
        uRecursionLoopSize = uLoopSize;
        uRecursionLoopCount = uLoopCount;
  if uRecursionStartIndex is not None:
    if gbDebugOutput: print ("Found recursion of %d loops of size %d at %d." % (
      uRecursionLoopCount,
      uRecursionLoopSize,
      uRecursionStartIndex,
    ));
    # We'll go back up the stack until we've found the first loop.
    # We'll hide all frames at the top of the stack up until the first loop:
    asLog=[];
    for uFrameIndex in range(uRecursionStartIndex):
      oLoopTerminatingFrame = oStack.aoFrames[uFrameIndex];
      oLoopTerminatingFrame.s0IsHiddenBecause = "This call is not part of the loop but happened to be involved in triggering the stack exhaustion exception";
      oLoopTerminatingFrame.bIsPartOfId = False;
      if gbDebugOutput: print("Hide: #%s %s (terminating frame)" % (
        oLoopTerminatingFrame.uIndex,
        oLoopTerminatingFrame.sb0SimplifiedAddress,
      ));
    while uRecursionStartIndex + uRecursionLoopSize < len(oStack.aoFrames):
      oCurrentLoopStartFrame = oStack.aoFrames[uRecursionStartIndex];
      oNextLoopStartFrame = oStack.aoFrames[uRecursionStartIndex + uRecursionLoopSize];
      if oCurrentLoopStartFrame.sbAddress != oNextLoopStartFrame.sbAddress:
        if gbDebugOutput: print("End of loops: #%s %s != #%s %s" % (
          oCurrentLoopStartFrame.uIndex,
          oCurrentLoopStartFrame.sb0SimplifiedAddress,
          oNextLoopStartFrame.uIndex,
          oNextLoopStartFrame.sb0SimplifiedAddress
        ));
        break;
      oCurrentLoopStartFrame.s0IsHiddenBecause = "This call is part of a secondary recursion loop";
      oCurrentLoopStartFrame.bIsPartOfId = False;
      uRecursionStartIndex += 1;
      if gbDebugOutput: print("Hide: #%s %s (secondary frame)" % (
        oCurrentLoopStartFrame.uIndex,
        oCurrentLoopStartFrame.sb0SimplifiedAddress,
      ));
    # Mark all frames in the first loop as part of the id:
    for uLoopFrameIndex in range(uRecursionLoopSize):
      oLoopFrame = oStack.aoFrames[uRecursionStartIndex + uLoopFrameIndex];
      oLoopFrame.bIsPartOfId = True;
      if gbDebugOutput: print("Id: #%s %s" % (
        oLoopFrame.uIndex,
        oLoopFrame.sb0SimplifiedAddress
      ));
    # Reverse the order of the stack frames in the id, so the first function
    # called in the loop is the first one in the Id.
    oBugReport.bTopDownStackInId = True;
    # The bug id and description are adjusted to explain the recursive function call as its cause.
    oBugReport.s0BugTypeId = "RecursiveCall(%d)" % uRecursionLoopSize;
    if uRecursionLoopSize == 1:
      oBugReport.s0BugDescription = "A recursive function call exhausted available stack memory";
    else:
      oBugReport.s0BugDescription = "A recursive function call involving %d functions exhausted available stack memory" % uRecursionLoopSize;
  return oBugReport;
