import re, threading;
from .cBugReport import cBugReport;
from .dxConfig import dxConfig;
from mMultiThreading import cLock;

bDebugOutput = False;
bDebugOutputCalculation = False;
bDebugOutputGetUsageData = False;
bDebugOutputWorm = False;

class cExcessiveCPUUsageDetector(object):
  def __init__(oSelf, oCdbWrapper):
    oSelf.oCdbWrapper = oCdbWrapper;
    oSelf.bStarted = False;
    oSelf.oLock = cLock(nzDeadlockTimeoutInSeconds = 1);
    oSelf.oCleanupTimeout = None;
    oSelf.oStartTimeout = None;
    oSelf.oCheckUsageTimeout = None;
    oSelf.oWormRunTimeout = None;
    oSelf.uWormBreakpointId = None;
    oSelf.uBugBreakpointId = None;
  
  def fStartTimeout(oSelf, nTimeoutInSeconds):
    if bDebugOutput: print "@@@ Starting excessive CPU usage checks in %d seconds..." % nTimeoutInSeconds;
    oCdbWrapper = oSelf.oCdbWrapper;
    oSelf.oLock.fAcquire();
    try:
      if oSelf.bStarted:
        # Stop any analysis timeouts in progress...
        if oSelf.oStartTimeout is not None:
          oCdbWrapper.fClearTimeout(oSelf.oStartTimeout);
          oSelf.oStartTimeout = None;
        if oSelf.oCheckUsageTimeout is not None:
          oCdbWrapper.fClearTimeout(oSelf.oCheckUsageTimeout);
          oSelf.oCheckUsageTimeout = None;
        oSelf.xPreviousData = None; # Previous data is no longer valid.
        # Request an immediate timeout to remove old breakpoints when the application is paused. This is needed because
        # we cannot execute any command while the application is still running, so these breakpoints cannot be removed
        # here.
        if oSelf.oCleanupTimeout is not None:
          oCdbWrapper.fClearTimeout(oSelf.oCleanupTimeout);
          oSelf.oCleanupTimeout = None;
        oSelf.oCleanupTimeout = oCdbWrapper.foSetTimeout(
          sDescription = "Cleanup for excessive CPU Usage detector",
          nTimeoutInSeconds = 0,
          fCallback = oSelf.fCleanup,
        );
      if nTimeoutInSeconds is not None:
        oSelf.oStartTimeout = oCdbWrapper.foSetTimeout(
          sDescription = "Start excessive CPU Usage detector",
          nTimeoutInSeconds = nTimeoutInSeconds, 
          fCallback = oSelf.fStart,
        );
    finally:
      oSelf.oLock.fRelease();
  
  def fCleanup(oSelf):
    # Remove old breakpoints; this is done in a timeout because we cannot execute any command while the application
    # is still running.
    oCdbWrapper = oSelf.oCdbWrapper;
    oSelf.oLock.fAcquire();
    try:
      if oSelf.oCleanupTimeout:
        oCdbWrapper.fClearTimeout(oSelf.oCleanupTimeout);
        oSelf.oCleanupTimeout = None;
        if bDebugOutput: print "@@@ Cleaning up excessive CPU usage breakpoints...";
        if oSelf.oWormRunTimeout:
          oCdbWrapper.fClearTimeout(oSelf.oWormRunTimeout);
          oSelf.oWormRunTimeout = None;
        if oSelf.uWormBreakpointId is not None:
          oCdbWrapper.fRemoveBreakpoint(oSelf.uWormBreakpointId);
          oSelf.uWormBreakpointId = None;
        if oSelf.uBugBreakpointId is not None:
          oCdbWrapper.fRemoveBreakpoint(oSelf.uBugBreakpointId);
          oSelf.uBugBreakpointId = None;
    finally:
      oSelf.oLock.fRelease();
  
  def fStart(oSelf):
    # A timeout to execute the cleanup function was set, but there is no guarantee the timeout has been fired yet; the
    # timeout to start this function may have been fired first. By calling the cleanup function now, we make sure that
    # cleanup happens if it has not already, and cancel the cleanup timeout if it has not yet fired.
    oSelf.bStarted = True;
    oSelf.fCleanup();
    if bDebugOutput: print "@@@ Start excessive CPU usage checks...";
    oCdbWrapper = oSelf.oCdbWrapper;
    oSelf.fGetUsageData();
    oSelf.oLock.fAcquire();
    try:
      oSelf.oCheckUsageTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "Check CPU usage for excessive CPU Usage detector",
        nTimeoutInSeconds = dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"],
        fCallback = oSelf.fCheckUsage,
      );
    finally:
      oSelf.oLock.fRelease();
  
  def fxMaxCPUUsage(oSelf):
    assert oSelf.oLock.bLocked, \
        "This method can only be called when the lock is acquired";
    ddnPreviousCPUTimeInSeconds_by_uThreadId_by_uProcessId = oSelf.ddnLastCPUTimeInSeconds_by_uThreadId_by_ProcessId;
    nPreviousRunTimeInSeconds = oSelf.nLastRunTimeInSeconds;
    oSelf.fGetUsageData();
    ddnCurrentCPUTimeInSeconds_by_uThreadId_by_uProcessId = oSelf.ddnLastCPUTimeInSeconds_by_uThreadId_by_ProcessId;
    nCurrentRunTimeInSeconds = oSelf.nLastRunTimeInSeconds;
    nRunTimeInSeconds = nCurrentRunTimeInSeconds - nPreviousRunTimeInSeconds;
    # Find out which thread in which process used the most CPU time by comparing previous CPU usage and
    # run time values to current values for all threads in all processes that exist in both data sets.
    nMaxCPUTimeInSeconds = 0;
    nMaxCPUUsagePercent = -1;
    nTotalCPUUsagePercent = 0;
    if bDebugOutputCalculation:
      print ",--- cExcessiveCPUUsageDetector.fGetUsageData ".ljust(120, "-");
      print "| Application run time: %.3f->%.3f=%.3f" % (nPreviousRunTimeInSeconds, nCurrentRunTimeInSeconds, nRunTimeInSeconds);
    uMaxCPUProcessId = None;
    for (uProcessId, dnCurrentCPUTimeInSeconds_by_uThreadId) in ddnCurrentCPUTimeInSeconds_by_uThreadId_by_uProcessId.items():
      if bDebugOutputCalculation:
        print ("|--- Process 0x%X" % uProcessId).ljust(120, "-");
        print "| %3s  %21s  %7s" % ("tid", "CPU time", "% Usage");
      dnPreviousCPUTimeInSeconds_by_uThreadId = ddnPreviousCPUTimeInSeconds_by_uThreadId_by_uProcessId.get(uProcessId, {});
      for (uThreadId, nCurrentCPUTimeInSeconds) in dnCurrentCPUTimeInSeconds_by_uThreadId.items():
        # nRunTimeInSeconds can be None due to a bug in cdb. In such cases, usage percentage cannot be calculated
        nPreviousCPUTimeInSeconds = dnPreviousCPUTimeInSeconds_by_uThreadId.get(uThreadId);
        if nPreviousCPUTimeInSeconds is not None and nCurrentCPUTimeInSeconds is not None:
          nCPUTimeInSeconds = nCurrentCPUTimeInSeconds - nPreviousCPUTimeInSeconds;
        else:
          nCPUTimeInSeconds = None;
        if nCPUTimeInSeconds is not None:
          nCPUUsagePercent = nRunTimeInSeconds > 0 and (100.0 * nCPUTimeInSeconds / nRunTimeInSeconds) or 0;
          nTotalCPUUsagePercent += nCPUUsagePercent;
          if nCPUUsagePercent > nMaxCPUUsagePercent:
            nMaxCPUTimeInSeconds = nCPUTimeInSeconds;
            nMaxCPUUsagePercent = nCPUUsagePercent;
            uMaxCPUProcessId = uProcessId;
            uMaxCPUThreadId = uThreadId;
        else:
          nCPUUsagePercent = None;
        if bDebugOutputCalculation:
          fsFormat = lambda nNumber: nNumber is None and " - " or ("%.3f" % nNumber);
          print "| %4X  %6s->%6s=%6s  %6s%%" % (
            uThreadId,
            fsFormat(nPreviousCPUTimeInSeconds), fsFormat(nCurrentCPUTimeInSeconds), fsFormat(nCPUTimeInSeconds),
            fsFormat(nCPUUsagePercent),
          );
    if uMaxCPUProcessId is None:
      if bDebugOutputCalculation:
        print "|".ljust(120, "-");
        print "| Insufficient data";
        print "'".ljust(120, "-");
      return None, None, None, None;
    if bDebugOutputCalculation:
      print "|".ljust(120, "-");
      print "| Total CPU usage: %d%%, max: %d%% for pid 0x%X, tid 0x%X" % \
         (nTotalCPUUsagePercent, nMaxCPUUsagePercent, uMaxCPUProcessId, uMaxCPUThreadId);
      print "'".ljust(120, "-");
    elif bDebugOutput:
      print "*** Total CPU usage: %d%%, max: %d%% for pid %d, tid %d" % \
          (nTotalCPUUsagePercent, nMaxCPUUsagePercent, uMaxCPUProcessId, uMaxCPUThreadId);
    # Rounding errors can give results > 100%. Fix that.
    if nTotalCPUUsagePercent > 100:
      nTotalCPUUsagePercent = 100.0;
    return uMaxCPUProcessId, uMaxCPUThreadId, nMaxCPUTimeInSeconds, nTotalCPUUsagePercent;
  
  def fCheckForExcessiveCPUUsage(oSelf, fCallback):
    if bDebugOutput: print "@@@ Checking for excessive CPU usage...";
    # We need to gather CPU Usage data now, wait nIntervalInSeconds and get it again to see if any thread is
    # currently using a lot of CPU:
    oSelf.fGetUsageData();
    def fExcessiveCPUUsageCheckIntervalTimeoutHandler(): # Called after the nIntervalInSeconds timeout fires.
      oSelf.oLock.fAcquire();
      try:
        uMaxCPUProcessId, uMaxCPUThreadId, nMaxCPUTimeInSeconds, nTotalCPUUsagePercent = oSelf.fxMaxCPUUsage();
        if uMaxCPUProcessId is None or nTotalCPUUsagePercent < dxConfig["nExcessiveCPUUsagePercent"]:
          # CPU usage is not considered excessive
          bExcessive = False;
        else:
          # Find out which function is using excessive CPU time in the most active thread.
          # (This will eventually trigger a bug report).
          oSelf.fInstallWorm(uMaxCPUProcessId, uMaxCPUThreadId, nTotalCPUUsagePercent);
          bExcessive = True;
      finally:
        oSelf.oLock.fRelease();
      fCallback(bExcessive);
    oSelf.oCdbWrapper.foSetTimeout(
      sDescription = "Check CPU usage for excessive CPU Usage detector",
      nTimeoutInSeconds = dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"],
      fCallback = fExcessiveCPUUsageCheckIntervalTimeoutHandler,
    );
  
  def fCheckUsage(oSelf):
    if bDebugOutput: print "@@@ Checking for excessive CPU usage...";
    oCdbWrapper = oSelf.oCdbWrapper;
    oSelf.oLock.fAcquire();
    try:
      if oSelf.oCheckUsageTimeout is None:
        return; # Analysis was stopped because a new timeout was set.
      oSelf.oCheckUsageTimeout = None;
      uMaxCPUProcessId, uMaxCPUThreadId, nMaxCPUTimeInSeconds, nTotalCPUUsagePercent = oSelf.fxMaxCPUUsage();
      if uMaxCPUProcessId is None:
        return; # No data available.
      # If all threads in all processes combined have excessive CPU usage
      if nTotalCPUUsagePercent >= dxConfig["nExcessiveCPUUsagePercent"]:
        # Find out which function is using excessive CPU time in the most active thread.
        oSelf.fInstallWorm(uMaxCPUProcessId, uMaxCPUThreadId, nTotalCPUUsagePercent);
      else:
        # No thread suspected of excessive CPU usage: measure CPU usage over another interval.
        oSelf.oCheckUsageTimeout = oCdbWrapper.foSetTimeout(
          sDescription = "Check CPU usage for excessive CPU Usage detector",
          nTimeoutInSeconds = dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"],
          fCallback = oSelf.fCheckUsage,
        );
    finally:
      oSelf.oLock.fRelease();
  
  def fWormDebugOutput(oSelf, sMessage, *auArguments):
    oCdbWrapper = oSelf.oCdbWrapper;
    asDebugOutput = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = '.printf "CPUUsage worm: %s\\r\\n"%s;' % \
          (sMessage, "".join([", 0x%X" % uArgument for uArgument in auArguments])),
      sComment = None,
      bShowOutputButNotCommandInHTMLReport = True,
    );
    assert len(asDebugOutput) == 1, "Unexpected output: %s" % repr(asDebugOutput);
    if bDebugOutputWorm: print "@@@ %3.3f %s" % (oCdbWrapper.nApplicationRunTimeInSeconds, asDebugOutput[0]);
  
  def fInstallWorm(oSelf, uProcessId, uThreadId, nTotalCPUUsagePercent):
    assert oSelf.oLock.bLocked, \
        "This method can only be called when the lock is acquired";
    if bDebugOutput: print "@@@ Installing excessive CPU usage worm...";
    oCdbWrapper = oSelf.oCdbWrapper;
    
    # Excessive CPU usage is assumed to be caused by code running in a loop for too long, causing the function that
    # contains the code to never return to its caller. The way a useful BugId is determined, is by finding an address
    # inside the looping code in this function, set a breakpoint there and report a bug when it is hit. The exact
    # instruction in this loop may change between runs, but the functions on the stack should not, and the latter is
    # used in the stack hash, giving you the same id for different tests of the same bug.
    # We already determined which process and thread used the most CPU, so the current instruction pointer for that
    # thread should be inside the loop, but it may in a function that was called by the looping function as part of the
    # loop. If so, this function should return. To find the one function on the stack that does not return, we create
    # a breakpoint "worm": whenever this breakpoint is hit, it moves up the stack by moving the breakpoint from its
    # current location to the current return address on the stack. Should the function in which the breakpoint was hit
    # return, the new breakpoint will be hit and the worm sets another breakpoint for the new return address. If the
    # function does not return, the breakpoint will not be hit and the worm will no longer move up the stack.
    # Every time a breakpoint is hit, its location is saved in a variable. After running some time, the application
    # is interrupted to set a breakpoint at the location of the last breakpoint that was hit. Since this is part of the
    # loop, it should get hit again, at which point a bug is reported. This allows us to get a stack inside the
    # function most likely to be the cause of the excessive CPU usage.
    
    # Select the relevant process and thread
    oCdbWrapper.fSelectProcessAndThread(uProcessId, uThreadId);
    oWormProcess = oCdbWrapper.oCdbCurrentProcess;
    oWormWindowsAPIThread = oCdbWrapper.oCdbCurrentWindowsAPIThread;
    oSelf.uProcessId = uProcessId;
    oSelf.uThreadId = uThreadId;
    oSelf.nTotalCPUUsagePercent = nTotalCPUUsagePercent;
    uInstructionPointer = oWormWindowsAPIThread.fuGetRegister("*ip");
    uStackPointer = oWormWindowsAPIThread.fuGetRegister("*sp");
# Ideally, we'de use the return address here but for some unknown reason cdb may not give a valid value at this point.
# However, we can use the instruction pointer to set our first breakpoint and when it is hit, the return addres will be
# correct... sigh.
#    uReturnAddress = oSelf.oWormProcess.fuGetValueForRegister("$ra", "Get return address");
    uBreakpointAddress = uInstructionPointer; # uReturnAddress would be preferred.
    oSelf.fWormDebugOutput(
      "Starting at IP=%p by creating a breakpoint at IP=%p, SP=%p...",
      uInstructionPointer, uBreakpointAddress, uStackPointer
    );
    oSelf.uLastInstructionPointer = uInstructionPointer;
    oSelf.uLastStackPointer = uStackPointer;
    oSelf.uNextBreakpointAddress = uBreakpointAddress;
    oSelf.uWormBreakpointId = oCdbWrapper.fuAddBreakpointForAddress(
      uAddress = uBreakpointAddress,
      fCallback = lambda uBreakpointId: oSelf.fMoveWormBreakpointUpTheStack(),
      uProcessId = oSelf.uProcessId,
      uThreadId = oSelf.uThreadId,
    );
    assert oSelf.uWormBreakpointId is not None, \
        "Could not create breakpoint at 0x%X" % oSelf.uLastInstructionPointer;
    oSelf.oWormRunTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "Start worm for excessive CPU Usage detector",
        nTimeoutInSeconds = dxConfig["nExcessiveCPUUsageWormRunTimeInSeconds"],
        fCallback = oSelf.fSetBugBreakpointAfterTimeout,
    );
  
  def fMoveWormBreakpointUpTheStack(oSelf):
    oCdbWrapper = oSelf.oCdbWrapper;
    oSelf.oLock.fAcquire();
    try:
      oCdbWrapper.fSelectProcessAndThread(oSelf.uProcessId, oSelf.uThreadId);
      oWormProcess = oCdbWrapper.oCdbCurrentProcess;
      oWormWindowsAPIThread = oCdbWrapper.oCdbCurrentWindowsAPIThread;
      uInstructionPointer = oWormWindowsAPIThread.fuGetRegister("*ip");
      uStackPointer = oWormWindowsAPIThread.fuGetRegister("*sp");
      # This is a sanity check: the instruction pointer should point to the instruction (or after the int3 instruction
      # inserted by cdb) where the breakpoint was set.
      assert uInstructionPointer in [oSelf.uNextBreakpointAddress, oSelf.uNextBreakpointAddress + 1], \
          "Expected to hit breakpoint at 0x%X, but got 0x%X instead !?" % \
          (oSelf.uNextBreakpointAddress, uInstructionPointer);
      # The code we're expecting to return to may actually be *called* in recursive code. We can detect this by checking
      # if the stackpointer has increased or not. If not, we have not yet returned and will ignore this breakpoint.
      if uStackPointer <= oSelf.uLastStackPointer:
        oSelf.fWormDebugOutput(
          "Ignored breakpoint at IP=%p, SP=%p: SP but must be >%p",
          uInstructionPointer, uStackPointer, oSelf.uLastStackPointer
        );
        return;
      uReturnAddress = oWormProcess.fuGetValueForRegister("$ra", "Get return address");
      if oSelf.uNextBreakpointAddress == uReturnAddress:
        oSelf.fWormDebugOutput(
          "Moving from IP=%p, SP=%p to IP=%p, SP=%p, by leaving breakpoint in place and adjusting expected SP...",
          uInstructionPointer, oSelf.uLastStackPointer, uReturnAddress, uStackPointer
        );
        # This is a recursive call, the breakpoint does not need to be moved.
        oSelf.uLastStackPointer = uStackPointer;
      else:
        oSelf.fWormDebugOutput(
          "Moving from IP=%p, SP=%p to IP=%p, SP=%p, by creating a new breakpoint...",
          uInstructionPointer, oSelf.uLastStackPointer, uReturnAddress, uStackPointer,
        );
        # Try to move the breakpoint to the return addess:
        uNewWormBreakpointId = oCdbWrapper.fuAddBreakpointForAddress(
          uAddress = uReturnAddress,
          fCallback = lambda uBreakpointId: oSelf.fMoveWormBreakpointUpTheStack(),
          uProcessId = oSelf.uProcessId,
          uThreadId = oSelf.uThreadId,
        );
        if uNewWormBreakpointId is None:
          # Could not move breakpoint: the return address may be invalid.
          # Ignore this and continue to run; the unchanged breakpoint may get hit again and we get another try, or
          # the timeout fires and we get a stack.
          oSelf.fWormDebugOutput(
            "Unable to create breakpoint at IP=%p: worm breakpoint remains at IP=%p, SP=%p...",
            uReturnAddress, uInstructionPointer, oSelf.uLastStackPointer,
          );
        else:
          oSelf.fWormDebugOutput(
            "Removing old breakpoint at IP=%p, SP=%p...",
            uInstructionPointer, oSelf.uLastStackPointer,
          );
          # Remove the old breakpoint.
          oCdbWrapper.fRemoveBreakpoint(oSelf.uWormBreakpointId);
          oSelf.uWormBreakpointId = uNewWormBreakpointId;
          oSelf.uLastInstructionPointer = uInstructionPointer;
          oSelf.uLastStackPointer = uStackPointer;
          oSelf.uNextBreakpointAddress = uReturnAddress;
      # The current timeout was for the function that just returned:
      # Start a new timeout for the function that is now executing.
      oCdbWrapper.fClearTimeout(oSelf.oWormRunTimeout);
      oSelf.oWormRunTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "End worm for excessive CPU Usage detector",
        nTimeoutInSeconds = dxConfig["nExcessiveCPUUsageWormRunTimeInSeconds"],
        fCallback = oSelf.fSetBugBreakpointAfterTimeout,
      );
    finally:
      oSelf.oLock.fRelease();

  def fSetBugBreakpointAfterTimeout(oSelf):
    # Ideally, we'd check here to make sure the application has actually been using CPU for
    # dxConfig["nExcessiveCPUUsageWormRunTimeInSeconds"] seconds since the last breakpoint was hit: if there were many
    # breakpoints, this will not be the case. Doing so should improve the reliability of the result.
    oCdbWrapper = oSelf.oCdbWrapper;
    if bDebugOutput: print "@@@ Worm run timeout: setting excessive CPU usage bug breakpoint...";
    oSelf.oLock.fAcquire();
    try:
      if oSelf.oWormRunTimeout is None:
        return; # Analysis was stopped because a new timeout was set.
      oSelf.oWormRunTimeout = None;
      oSelf.fWormDebugOutput(
        "Run timeout; stopping worm and creating bug breakpoint...",
      );
      # Remove worm breakpoint
      oSelf.fWormDebugOutput(
        "Removing old worm breakpoint at IP=%p, SP=%p...",
        oSelf.uLastInstructionPointer, oSelf.uLastStackPointer,
      );
      oCdbWrapper.fRemoveBreakpoint(oSelf.uWormBreakpointId);
      oSelf.uWormBreakpointId = None;
      # Set bug breakpoint
      oSelf.fWormDebugOutput(
        "Creating bug breakpoint at IP=%p, SP=%p...",
        oSelf.uLastInstructionPointer, oSelf.uLastStackPointer
      );
      oSelf.uBugBreakpointId = oCdbWrapper.fuAddBreakpointForAddress(
        uAddress = oSelf.uLastInstructionPointer,
        fCallback = lambda uBreakpointId: oSelf.fReportCPUUsageBug(),
        uProcessId = oSelf.uProcessId,
        uThreadId = oSelf.uThreadId,
      );
      oSelf.uNextBreakpointAddress = oSelf.uLastInstructionPointer;
      assert oSelf.uBugBreakpointId is not None, \
         "Could not set breakpoint at 0x%X" % oSelf.uLastInstructionPointer;
    finally:
      oSelf.oLock.fRelease();
  
  def fReportCPUUsageBug(oSelf):
    oCdbWrapper = oSelf.oCdbWrapper;
    oSelf.oLock.fAcquire();
    try:
      oCdbWrapper.fSelectProcessAndThread(oSelf.uProcessId, oSelf.uThreadId);
      oWormProcess = oCdbWrapper.oCdbCurrentProcess;
      oWormWindowsAPIThread = oCdbWrapper.oCdbCurrentWindowsAPIThread;
      uStackPointer = oWormWindowsAPIThread.fuGetRegister("*sp");
      uInstructionPointer = oWormWindowsAPIThread.fuGetRegister("*ip");
      # This is a sanity check: the instruction pointer should point to the instruction (or after the int3 instruction
      # inserted by cdb) where the breakpoint was set.
      assert uInstructionPointer in [oSelf.uNextBreakpointAddress, oSelf.uNextBreakpointAddress + 1], \
          "Expected to hit breakpoint at 0x%X, but got 0x%X instead !?" % \
          (oSelf.uNextBreakpointAddress, uInstructionPointer);
      # The code we're expecting to return to may actually be *called* in recursive code. We can detect this by checking
      # if the stackpointer has increased or not. If not, we have not yet returned and will ignore this breakpoint.
      if uStackPointer < oSelf.uLastStackPointer:
        oSelf.fWormDebugOutput(
          "Ignored bug breakpoint at IP=%p, SP=%p: SP but must be >=%p",
          uInstructionPointer, uStackPointer, oSelf.uLastStackPointer
        );
        return;
      if bDebugOutput: print "@@@ Reporting excessive CPU usage bug...";
      oSelf.fWormDebugOutput(
        "Bug breakpoint at IP=%p, SP=%p is hit, removing breakpoint and reporting bug...",
        uInstructionPointer, uStackPointer,
      );
      # Remove the breakpoint
      oCdbWrapper.fRemoveBreakpoint(oSelf.uBugBreakpointId);
      oSelf.uBugBreakpointId = None;
      # Report a bug
      sBugTypeId = "CPUUsage";
      sBugDescription = "The application was using %d%% CPU for %d seconds, which is considered excessive." % \
          (oSelf.nTotalCPUUsagePercent, dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"]);
      sSecurityImpact = None;
      oBugReport = cBugReport.foCreate(oWormProcess, oWormWindowsAPIThread, sBugTypeId, sBugDescription, sSecurityImpact);
      oBugReport.bRegistersRelevant = False;
      oBugReport.fReport(oCdbWrapper);
      oCdbWrapper.fStop();
    finally:
      oSelf.oLock.fRelease();
  
  def fGetUsageData(oSelf):
    oCdbWrapper = oSelf.oCdbWrapper;
    # Get the amount of CPU time each thread in each process has consumed
    ddnCPUTimeInSeconds_by_uThreadId_by_uProcessId = {};
    sTimeType = None;
    if bDebugOutputGetUsageData:
      print ",--- cExcessiveCPUUsageDetector.fGetUsageData ".ljust(120, "-");
    for uProcessId in oCdbWrapper.doProcess_by_uId.keys():
      if bDebugOutputGetUsageData:
        print ("|--- Process 0x%X" % uProcessId).ljust(120, "-");
        print "| %4s  %6s  %s" % ("tid", "time", "source line");
      oCdbWrapper.fSelectProcess(uProcessId);
      asThreadTimes = oCdbWrapper.fasExecuteCdbCommand(
        sCommand = "!runaway 7;",
        sComment = "Get CPU usage information",
      );
      dnCPUTimeInSeconds_by_uThreadId = {};
      dnCPUTimeInSeconds_by_uThreadId = ddnCPUTimeInSeconds_by_uThreadId_by_uProcessId[uProcessId] = {};
      for sLine in asThreadTimes:
        if re.match(r"^\s*(Thread\s+Time)\s*$", sLine):
          pass; # Header, ignored.
        elif re.match(r"^\s*(User Mode Time|Kernel Mode Time|Elapsed Time)\s*$", sLine):
          sTimeType = sLine.strip(); # Keep track of what type of type of times are being reported.
        else:
          assert sTimeType is not None, \
              "Expected a header before values in %s.\r\n%s" % (sLine, "\r\n".join(asThreadTimes));
          oThreadTime = re.match(r"^\s*\d+:(\w+)\s+ (\d+) days (\d\d?):(\d\d):(\d\d.\d\d\d)\s*$", sLine);
          assert oThreadTime, \
              "Unrecognized \"!runaway3\" output: %s\r\n%s" % (sLine, "\r\n".join(asThreadTimes));
          sThreadId, sDays, sHours, sMinutes, sSecondsMilliseconds = oThreadTime.groups();
          uThreadId = int(sThreadId, 16);
          nTimeInSeconds = ((long(sDays) * 24 + long(sHours)) * 60 + long(sMinutes)) * 60 + float(sSecondsMilliseconds);
          if nTimeInSeconds >= 2000000000:
            # Due to a bug in !runaway, elapsed time sometimes gets reported as a very, very large number.
            assert sTimeType == "Elapsed Time", \
                "Unexpected large value for %s: %s\r\n%s" % (sTimeType, nTimeInSeconds, "\r\n".join(asThreadTimes));
            # In such cases, do not return a value for elapsed time.
            nTimeInSeconds = None;
  # Use for debugging
          if sTimeType == "User Mode Time":
            dnCPUTimeInSeconds_by_uThreadId[uThreadId] = nTimeInSeconds;
            if bDebugOutputGetUsageData: print "| %4X  %6s %s" % (uThreadId, nTimeInSeconds is None and "?" or ("%.3f" % nTimeInSeconds), repr(sLine));
          elif sTimeType == "Kernel Mode Time":
            dnCPUTimeInSeconds_by_uThreadId[uThreadId] += nTimeInSeconds;
            if bDebugOutputGetUsageData: print "| %4X  %6s %s" % (uThreadId, nTimeInSeconds is None and "?" or ("+%.3f" % nTimeInSeconds), repr(sLine));
    if bDebugOutputGetUsageData: print "'".ljust(120, "-");
    oSelf.ddnLastCPUTimeInSeconds_by_uThreadId_by_ProcessId = ddnCPUTimeInSeconds_by_uThreadId_by_uProcessId;
    oSelf.nLastRunTimeInSeconds = oCdbWrapper.nApplicationRunTimeInSeconds;
