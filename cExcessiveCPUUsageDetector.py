import re, threading;
from cBugReport import cBugReport;
from dxConfig import dxConfig;

bDebugOutput = False;
bDebugOutputCalculation = False;
bDebugOutputGetUsageData = False;
bDebugOutputWorm = False;

class cExcessiveCPUUsageDetector(object):
  def __init__(oExcessiveCPUUsageDetector, oCdbWrapper):
    oExcessiveCPUUsageDetector.oCdbWrapper = oCdbWrapper;
    oExcessiveCPUUsageDetector.bStarted = False;
    oExcessiveCPUUsageDetector.oLock = threading.Lock();
    oExcessiveCPUUsageDetector.oCleanupTimeout = None;
    oExcessiveCPUUsageDetector.oStartTimeout = None;
    oExcessiveCPUUsageDetector.oCheckUsageTimeout = None;
    oExcessiveCPUUsageDetector.oWormRunTimeout = None;
    oExcessiveCPUUsageDetector.uWormBreakpointId = None;
    oExcessiveCPUUsageDetector.uBugBreakpointId = None;
  
  def fStartTimeout(oExcessiveCPUUsageDetector, nTimeout):
    if bDebugOutput: print "@@@ Starting excessive CPU usage checks in %d seconds..." % nTimeout;
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    oExcessiveCPUUsageDetector.oLock.acquire();
    try:
      if oExcessiveCPUUsageDetector.bStarted:
        # Stop any analysis timeouts in progress...
        if oExcessiveCPUUsageDetector.oStartTimeout is not None:
          oCdbWrapper.fClearTimeout(oExcessiveCPUUsageDetector.oStartTimeout);
          oExcessiveCPUUsageDetector.oStartTimeout = None;
        if oExcessiveCPUUsageDetector.oCheckUsageTimeout is not None:
          oCdbWrapper.fClearTimeout(oExcessiveCPUUsageDetector.oCheckUsageTimeout);
          oExcessiveCPUUsageDetector.oCheckUsageTimeout = None;
        oExcessiveCPUUsageDetector.xPreviousData = None; # Previous data is no longer valid.
        # Request an immediate timeout to remove old breakpoints when the application is paused. This is needed because
        # we cannot execute any command while the application is still running, so these breakpoints cannot be removed
        # here.
        if oExcessiveCPUUsageDetector.oCleanupTimeout is not None:
          oCdbWrapper.fClearTimeout(oExcessiveCPUUsageDetector.oCleanupTimeout);
          oExcessiveCPUUsageDetector.oCleanupTimeout = None;
        oExcessiveCPUUsageDetector.oCleanupTimeout = oCdbWrapper.foSetTimeout(
          sDescription = "Cleanup for excessive CPU Usage detector",
          nTimeToWait = 0,
          fCallback = oExcessiveCPUUsageDetector.fCleanup,
        );
      if nTimeout is not None:
        oExcessiveCPUUsageDetector.oStartTimeout = oCdbWrapper.foSetTimeout(
          sDescription = "Start excessive CPU Usage detector",
          nTimeToWait = nTimeout, 
          fCallback = oExcessiveCPUUsageDetector.fStart,
        );
    finally:
      oExcessiveCPUUsageDetector.oLock.release();
  
  def fCleanup(oExcessiveCPUUsageDetector):
    # Remove old breakpoints; this is done in a timeout because we cannot execute any command while the application
    # is still running.
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    oExcessiveCPUUsageDetector.oLock.acquire();
    try:
      if oExcessiveCPUUsageDetector.oCleanupTimeout:
        oCdbWrapper.fClearTimeout(oExcessiveCPUUsageDetector.oCleanupTimeout);
        oExcessiveCPUUsageDetector.oCleanupTimeout = None;
        if bDebugOutput: print "@@@ Cleaning up excessive CPU usage breakpoints...";
        if oExcessiveCPUUsageDetector.oWormRunTimeout:
          oCdbWrapper.fClearTimeout(oExcessiveCPUUsageDetector.oWormRunTimeout);
          oExcessiveCPUUsageDetector.oWormRunTimeout = None;
        if oExcessiveCPUUsageDetector.uWormBreakpointId is not None:
          oCdbWrapper.fRemoveBreakpoint(oExcessiveCPUUsageDetector.uWormBreakpointId);
          oExcessiveCPUUsageDetector.uWormBreakpointId = None;
        if oExcessiveCPUUsageDetector.uBugBreakpointId is not None:
          oCdbWrapper.fRemoveBreakpoint(oExcessiveCPUUsageDetector.uBugBreakpointId);
          oExcessiveCPUUsageDetector.uBugBreakpointId = None;
    finally:
      oExcessiveCPUUsageDetector.oLock.release();
  
  def fStart(oExcessiveCPUUsageDetector):
    # A timeout to execute the cleanup function was set, but there is no guarantee the timeout has been fired yet; the
    # timeout to start this function may have been fired first. By calling the cleanup function now, we make sure that
    # cleanup happens if it has not already, and cancel the cleanup timeout if it has not yet fired.
    oExcessiveCPUUsageDetector.bStarted = True;
    oExcessiveCPUUsageDetector.fCleanup();
    if bDebugOutput: print "@@@ Start excessive CPU usage checks...";
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    oExcessiveCPUUsageDetector.fGetUsageData();
    oExcessiveCPUUsageDetector.oLock.acquire();
    try:
      oExcessiveCPUUsageDetector.oCheckUsageTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "Check CPU usage for excessive CPU Usage detector",
        nTimeToWait = dxConfig["nExcessiveCPUUsageCheckInterval"],
        fCallback = oExcessiveCPUUsageDetector.fCheckUsage,
      );
    finally:
      oExcessiveCPUUsageDetector.oLock.release();
  
  def fxMaxCPUUsage(oExcessiveCPUUsageDetector):
    # NO LOCK! Called from method that already locked it.
    ddnPreviousCPUTime_by_uThreadId_by_uProcessId = oExcessiveCPUUsageDetector.ddnLastCPUTime_by_uThreadId_by_ProcessId;
    nPreviousRunTime = oExcessiveCPUUsageDetector.nLastRunTime;
    oExcessiveCPUUsageDetector.fGetUsageData();
    ddnCurrentCPUTime_by_uThreadId_by_uProcessId = oExcessiveCPUUsageDetector.ddnLastCPUTime_by_uThreadId_by_ProcessId;
    nCurrentRunTime = oExcessiveCPUUsageDetector.nLastRunTime;
    nRunTime = nCurrentRunTime - nPreviousRunTime;
    # Find out which thread in which process used the most CPU time by comparing previous CPU usage and
    # run time values to current values for all threads in all processes that exist in both data sets.
    nMaxCPUTime = 0;
    nMaxCPUUsagePercent = -1;
    nTotalCPUUsagePercent = 0;
    if bDebugOutputCalculation:
      print ",--- cExcessiveCPUUsageDetector.fGetUsageData ".ljust(120, "-");
      print "| Application run time: %.3f->%.3f=%.3f" % (nPreviousRunTime, nCurrentRunTime, nRunTime);
    uMaxCPUProcessId = None;
    for (uProcessId, dnCurrentCPUTime_by_uThreadId) in ddnCurrentCPUTime_by_uThreadId_by_uProcessId.items():
      if bDebugOutputCalculation:
        print ("|--- Process 0x%X" % uProcessId).ljust(120, "-");
        print "| %3s  %21s  %7s" % ("tid", "CPU time", "% Usage");
      dnPreviousCPUTime_by_uThreadId = ddnPreviousCPUTime_by_uThreadId_by_uProcessId.get(uProcessId, {});
      for (uThreadId, nCurrentCPUTime) in dnCurrentCPUTime_by_uThreadId.items():
        # nRunTime can be None due to a bug in cdb. In such cases, usage percentage cannot be calculated
        nPreviousCPUTime = dnPreviousCPUTime_by_uThreadId.get(uThreadId);
        if nPreviousCPUTime is not None and nCurrentCPUTime is not None:
          nCPUTime = nCurrentCPUTime - nPreviousCPUTime;
        else:
          nCPUTime = None;
        if nCPUTime is not None:
          nCPUUsagePercent = nRunTime > 0 and (100.0 * nCPUTime / nRunTime) or 0;
          nTotalCPUUsagePercent += nCPUUsagePercent;
          if nCPUUsagePercent > nMaxCPUUsagePercent:
            nMaxCPUTime = nCPUTime;
            nMaxCPUUsagePercent = nCPUUsagePercent;
            uMaxCPUProcessId = uProcessId;
            uMaxCPUThreadId = uThreadId;
        else:
          nCPUUsagePercent = None;
        if bDebugOutputCalculation:
          fsFormat = lambda nNumber: nNumber is None and " - " or ("%.3f" % nNumber);
          print "| %4X  %6s->%6s=%6s  %6s%%" % (
            uThreadId,
            fsFormat(nPreviousCPUTime), fsFormat(nCurrentCPUTime), fsFormat(nCPUTime),
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
    return uMaxCPUProcessId, uMaxCPUThreadId, nMaxCPUTime, nTotalCPUUsagePercent;

  def fCheckUsage(oExcessiveCPUUsageDetector):
    if bDebugOutput: print "@@@ Checking for excessive CPU usage...";
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    oExcessiveCPUUsageDetector.oLock.acquire();
    try:
      if oExcessiveCPUUsageDetector.oCheckUsageTimeout is None:
        return; # Analysis was stopped because a new timeout was set.
      oExcessiveCPUUsageDetector.oCheckUsageTimeout = None;
      uMaxCPUProcessId, uMaxCPUThreadId, nMaxCPUTime, nTotalCPUUsagePercent = oExcessiveCPUUsageDetector.fxMaxCPUUsage();
      if uMaxCPUProcessId is None:
        return; # No data available.
      # If all threads in all processes combined have excessive CPU usage
      if nTotalCPUUsagePercent > dxConfig["nExcessiveCPUUsagePercent"]:
        # Find out which function is using excessive CPU time in the most active thread.
        oExcessiveCPUUsageDetector.fInstallWorm(uMaxCPUProcessId, uMaxCPUThreadId, nTotalCPUUsagePercent);
      else:
        # No thread suspected of excessive CPU usage: measure CPU usage over another interval.
        oExcessiveCPUUsageDetector.oCheckUsageTimeout = oCdbWrapper.foSetTimeout(
          sDescription = "Check CPU usage for excessive CPU Usage detector",
          nTimeToWait = dxConfig["nExcessiveCPUUsageCheckInterval"],
          fCallback = oExcessiveCPUUsageDetector.fCheckUsage,
        );
    finally:
      oExcessiveCPUUsageDetector.oLock.release();
  
  def fWormDebugOutput(oExcessiveCPUUsageDetector, sMessage, *auArguments):
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    asDebugOutput = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = '.printf "CPUUsage worm: %s\\r\\n"%s;' % \
          (sMessage, "".join([", 0x%X" % uArgument for uArgument in auArguments])),
      sComment = None,
      bShowOutputButNotCommandInHTMLReport = True,
    );
    assert len(asDebugOutput) == 1, "Unexpected output: %s" % repr(asDebugOutput);
    if bDebugOutputWorm: print "@@@ %3.3f %s" % (oCdbWrapper.nApplicationRunTime, asDebugOutput[0]);
  
  def fInstallWorm(oExcessiveCPUUsageDetector, uProcessId, uThreadId, nTotalCPUUsagePercent):
    if bDebugOutput: print "@@@ Installing excessive CPU usage worm...";
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    # NO LOCK! Called from method that already locked it.
    
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
    oWormProcess = oCdbWrapper.oCurrentProcess;
    oExcessiveCPUUsageDetector.uProcessId = uProcessId;
    oExcessiveCPUUsageDetector.uThreadId = uThreadId;
    oExcessiveCPUUsageDetector.nTotalCPUUsagePercent = nTotalCPUUsagePercent;
    uInstructionPointer = oWormProcess.fuGetValueForRegister("$ip", "Get instruction pointer");
    uStackPointer = oWormProcess.fuGetValueForRegister("$csp", "Get stack pointer");
# Ideally, we'de use the return address here but for some unknown reason cdb may not give a valid value at this point.
# However, we can use the instruction pointer to set our first breakpoint and when it is hit, the return addres will be
# correct... sigh.
#    uReturnAddress = oExcessiveCPUUsageDetector.oWormProcess.fuGetValueForRegister("$ra", "Get return address");
    uBreakpointAddress = uInstructionPointer; # uReturnAddress would be preferred.
    oExcessiveCPUUsageDetector.fWormDebugOutput(
      "Starting at IP=%p by creating a breakpoint at IP=%p, SP=%p...",
      uInstructionPointer, uBreakpointAddress, uStackPointer
    );
    oExcessiveCPUUsageDetector.uLastInstructionPointer = uInstructionPointer;
    oExcessiveCPUUsageDetector.uLastStackPointer = uStackPointer;
    oExcessiveCPUUsageDetector.uNextBreakpointAddress = uBreakpointAddress;
    oExcessiveCPUUsageDetector.uWormBreakpointId = oCdbWrapper.fuAddBreakpoint(
      uAddress = uBreakpointAddress,
      fCallback = lambda uBreakpointId: oExcessiveCPUUsageDetector.fMoveWormBreakpointUpTheStack(),
      uProcessId = oExcessiveCPUUsageDetector.uProcessId,
      uThreadId = oExcessiveCPUUsageDetector.uThreadId,
    );
    assert oExcessiveCPUUsageDetector.uWormBreakpointId is not None, \
        "Could not create breakpoint at 0x%X" % oExcessiveCPUUsageDetector.uLastInstructionPointer;
    oExcessiveCPUUsageDetector.oWormRunTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "Start worm for excessive CPU Usage detector",
        nTimeToWait = dxConfig["nExcessiveCPUUsageWormRunTime"],
        fCallback = oExcessiveCPUUsageDetector.fSetBugBreakpointAfterTimeout,
    );
  
  def fMoveWormBreakpointUpTheStack(oExcessiveCPUUsageDetector):
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    oExcessiveCPUUsageDetector.oLock.acquire();
    try:
      oCdbWrapper.fSelectProcessAndThread(oExcessiveCPUUsageDetector.uProcessId, oExcessiveCPUUsageDetector.uThreadId);
      oWormProcess = oCdbWrapper.oCurrentProcess;
      uStackPointer = oWormProcess.fuGetValueForRegister("$csp", "Get stack pointer");
      uInstructionPointer = oWormProcess.fuGetValueForRegister("$ip", "Get instruction pointer");
      # This is a sanity check: the instruction pointer should be equal to the address at which we set the breakpoint.
      assert uInstructionPointer == oExcessiveCPUUsageDetector.uNextBreakpointAddress, \
          "Expected to hit breakpoint at 0x%X, but got 0x%X instead !?" % (oExcessiveCPUUsageDetector.uNextBreakpointAddress, uInstructionPointer);
      # The code we're expecting to return to may actually be *called* in recursive code. We can detect this by checking
      # if the stackpointer has increased or not. If not, we have not yet returned and will ignore this breakpoint.
      if uStackPointer <= oExcessiveCPUUsageDetector.uLastStackPointer:
        oExcessiveCPUUsageDetector.fWormDebugOutput(
          "Ignored breakpoint at IP=%p, SP=%p: SP but must be >%p",
          uInstructionPointer, uStackPointer, oExcessiveCPUUsageDetector.uLastStackPointer
        );
        return;
      uReturnAddress = oWormProcess.fuGetValueForRegister("$ra", "Get return address");
      if uInstructionPointer == uReturnAddress:
        oExcessiveCPUUsageDetector.fWormDebugOutput(
          "Moving from IP=%p, SP=%p to IP=%p, SP=%p, by leaving breakpoint in place and adjusting expected SP...",
          uInstructionPointer, oExcessiveCPUUsageDetector.uLastStackPointer, uReturnAddress, uStackPointer
        );
        # This is a recursive call, the breakpoint does not need to be moved.
        oExcessiveCPUUsageDetector.uLastStackPointer = uStackPointer;
      else:
        oExcessiveCPUUsageDetector.fWormDebugOutput(
          "Moving from IP=%p, SP=%p to IP=%p, SP=%p, by creating a new breakpoint...",
          uInstructionPointer, oExcessiveCPUUsageDetector.uLastStackPointer, uReturnAddress, uStackPointer,
        );
        # Try to move the breakpoint to the return addess:
        uNewWormBreakpointId = oCdbWrapper.fuAddBreakpoint(
          uAddress = uReturnAddress,
          fCallback = lambda uBreakpointId: oExcessiveCPUUsageDetector.fMoveWormBreakpointUpTheStack(),
          uProcessId = oExcessiveCPUUsageDetector.uProcessId,
          uThreadId = oExcessiveCPUUsageDetector.uThreadId,
        );
        if uNewWormBreakpointId is None:
          # Could not move breakpoint: the return address may be invalid.
          # Ignore this and continue to run; the unchanged breakpoint may get hit again and we get another try, or
          # the timeout fires and we get a stack.
          oExcessiveCPUUsageDetector.fWormDebugOutput(
            "Unable to create breakpoint at IP=%p: worm breakpoint remains at IP=%p, SP=%p...",
            uReturnAddress, uInstructionPointer, oExcessiveCPUUsageDetector.uLastStackPointer,
          );
        else:
          oExcessiveCPUUsageDetector.fWormDebugOutput(
            "Removing old breakpoint at IP=%p, SP=%p...",
            uInstructionPointer, oExcessiveCPUUsageDetector.uLastStackPointer,
          );
          # Remove the old breakpoint.
          oCdbWrapper.fRemoveBreakpoint(oExcessiveCPUUsageDetector.uWormBreakpointId);
          oExcessiveCPUUsageDetector.uWormBreakpointId = uNewWormBreakpointId;
          oExcessiveCPUUsageDetector.uLastInstructionPointer = uInstructionPointer;
          oExcessiveCPUUsageDetector.uLastStackPointer = uStackPointer;
          oExcessiveCPUUsageDetector.uNextBreakpointAddress = uReturnAddress;
      # The current timeout was for the function that just returned:
      # Start a new timeout for the function that is now executing.
      oCdbWrapper.fClearTimeout(oExcessiveCPUUsageDetector.oWormRunTimeout);
      oExcessiveCPUUsageDetector.oWormRunTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "End worm for excessive CPU Usage detector",
        nTimeToWait = dxConfig["nExcessiveCPUUsageWormRunTime"],
        fCallback = oExcessiveCPUUsageDetector.fSetBugBreakpointAfterTimeout,
      );
    finally:
      oExcessiveCPUUsageDetector.oLock.release();

  def fSetBugBreakpointAfterTimeout(oExcessiveCPUUsageDetector):
    # Ideally, we'd check here to make sure the application has actually been using CPU for
    # dxConfig["nExcessiveCPUUsageWormRunTime"] seconds since the last breakpoint was hit: if there were many
    # breakpoints, this will not be the case. Doing so should improve the reliability of the result.
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    if bDebugOutput: print "@@@ Worm run timeout: setting excessive CPU usage bug breakpoint...";
    oExcessiveCPUUsageDetector.oLock.acquire();
    try:
      if oExcessiveCPUUsageDetector.oWormRunTimeout is None:
        return; # Analysis was stopped because a new timeout was set.
      oExcessiveCPUUsageDetector.oWormRunTimeout = None;
      oExcessiveCPUUsageDetector.fWormDebugOutput(
        "Run timeout; stopping worm and creating bug breakpoint...",
      );
      # Remove worm breakpoint
      oExcessiveCPUUsageDetector.fWormDebugOutput(
        "Removing old worm breakpoint at IP=%p, SP=%p...",
        oExcessiveCPUUsageDetector.uLastInstructionPointer, oExcessiveCPUUsageDetector.uLastStackPointer,
      );
      oCdbWrapper.fRemoveBreakpoint(oExcessiveCPUUsageDetector.uWormBreakpointId);
      oExcessiveCPUUsageDetector.uWormBreakpointId = None;
      # Set bug breakpoint
      oExcessiveCPUUsageDetector.fWormDebugOutput(
        "Creating bug breakpoint at IP=%p, SP=%p...",
        oExcessiveCPUUsageDetector.uLastInstructionPointer, oExcessiveCPUUsageDetector.uLastStackPointer
      );
      oExcessiveCPUUsageDetector.uBugBreakpointId = oCdbWrapper.fuAddBreakpoint(
        uAddress = oExcessiveCPUUsageDetector.uLastInstructionPointer,
        fCallback = lambda uBreakpointId: oExcessiveCPUUsageDetector.fReportCPUUsageBug(),
        uProcessId = oExcessiveCPUUsageDetector.uProcessId,
        uThreadId = oExcessiveCPUUsageDetector.uThreadId,
      );
      oExcessiveCPUUsageDetector.uNextBreakpointAddress = oExcessiveCPUUsageDetector.uLastInstructionPointer;
      assert oExcessiveCPUUsageDetector.uBugBreakpointId is not None, \
         "Could not set breakpoint at 0x%X" % oExcessiveCPUUsageDetector.uLastInstructionPointer;
    finally:
      oExcessiveCPUUsageDetector.oLock.release();
  
  def fReportCPUUsageBug(oExcessiveCPUUsageDetector):
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    oExcessiveCPUUsageDetector.oLock.acquire();
    try:
      oCdbWrapper.fSelectProcessAndThread(oExcessiveCPUUsageDetector.uProcessId, oExcessiveCPUUsageDetector.uThreadId);
      oWormProcess = oCdbWrapper.oCurrentProcess;
      uStackPointer = oWormProcess.fuGetValueForRegister("$csp", "Get stack pointer");
      uInstructionPointer = oWormProcess.fuGetValueForRegister("$ip", "Get instruction pointer");
      # This is a sanity check: the instruction pointer should be equal to the address at which we set the breakpoint.
      assert uInstructionPointer == oExcessiveCPUUsageDetector.uNextBreakpointAddress, \
          "Expected to hit breakpoint at 0x%X, but got 0x%X instead !?" % (oExcessiveCPUUsageDetector.uNextBreakpointAddress, uInstructionPointer);
      # The code we're expecting to return to may actually be *called* in recursive code. We can detect this by checking
      # if the stackpointer has increased or not. If not, we have not yet returned and will ignore this breakpoint.
      if uStackPointer < oExcessiveCPUUsageDetector.uLastStackPointer:
        oExcessiveCPUUsageDetector.fWormDebugOutput(
          "Ignored bug breakpoint at IP=%p, SP=%p: SP but must be >=%p",
          uInstructionPointer, uStackPointer, oExcessiveCPUUsageDetector.uLastStackPointer
        );
        return;
      if bDebugOutput: print "@@@ Reporting excessive CPU usage bug...";
      oExcessiveCPUUsageDetector.fWormDebugOutput(
        "Bug breakpoint at IP=%p, SP=%p is hit, removing breakpoint and reporting bug...",
        uInstructionPointer, uStackPointer,
      );
      # Remove the breakpoint
      oCdbWrapper.fRemoveBreakpoint(oExcessiveCPUUsageDetector.uBugBreakpointId);
      oExcessiveCPUUsageDetector.uBugBreakpointId = None;
      # Report a bug
      sBugTypeId = "CPUUsage";
      sBugDescription = "The application was using %d%% CPU for %d seconds, which is considered excessive." % \
          (oExcessiveCPUUsageDetector.nTotalCPUUsagePercent, dxConfig["nExcessiveCPUUsageCheckInterval"]);
      sSecurityImpact = None;
      oBugReport = cBugReport.foCreate(oWormProcess, sBugTypeId, sBugDescription, sSecurityImpact);
      oBugReport.bRegistersRelevant = False;
      oBugReport.fReport(oCdbWrapper);
      oCdbWrapper.bFatalBugDetected = True;
    finally:
      oExcessiveCPUUsageDetector.oLock.release();
  
  def fGetUsageData(oExcessiveCPUUsageDetector):
    oCdbWrapper = oExcessiveCPUUsageDetector.oCdbWrapper;
    # Get the amount of CPU time each thread in each process has consumed
    ddnCPUTime_by_uThreadId_by_uProcessId = {};
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
      dnCPUTime_by_uThreadId = {};
      dnCPUTime_by_uThreadId = ddnCPUTime_by_uThreadId_by_uProcessId[uProcessId] = {};
      for sLine in asThreadTimes:
        if re.match(r"^\s*(Thread\s+Time)\s*$", sLine):
          pass; # Header, ignored.
        elif re.match(r"^\s*(User Mode Time|Kernel Mode Time|Elapsed Time)\s*$", sLine):
          sTimeType = sLine.strip(); # Keep track of what type of type of times are being reported.
        else:
          assert sTimeType is not None, \
              "Expected a header before values in %s.\r\n%s" % (sLine, "\r\n".join(asThreadTimes));
          oThreadTime = re.match(r"^\s*\d+:(\w+)\s+ (\d+) days (\d\d?):(\d\d):(\d\d).(\d\d\d)\s*$", sLine);
          assert oThreadTime, \
              "Unrecognized \"!runaway3\" output: %s\r\n%s" % (sLine, "\r\n".join(asThreadCPUTime));
          sThreadId, sDays, sHours, sMinutes, sSeconds, sMilliseconds = oThreadTime.groups();
          uThreadId = int(sThreadId, 16);
          nTime = ((long(sDays) * 24 + long(sHours)) * 60 + long(sMinutes)) * 60 + long(sSeconds) + long(sMilliseconds) / 1000.0;
          if nTime >= 2000000000:
            # Due to a bug in !runaway, elapsed time sometimes gets reported as a very, very large number.
            assert sTimeType == "Elapsed Time", \
                "Unexpected large value for %s: %s\r\n%s" % (sTimeType, nTime, "\r\n".join(asThreadCPUTime));
            # In such cases, do not return a value for elapsed time.
            nTime = None;
  # Use for debugging
          if sTimeType == "User Mode Time":
            dnCPUTime_by_uThreadId[uThreadId] = nTime;
            if bDebugOutputGetUsageData: print "| %4X  %6s %s" % (uThreadId, nTime is None and "?" or ("%.3f" % nTime), repr(sLine));
          elif sTimeType == "Kernel Mode Time":
            dnCPUTime_by_uThreadId[uThreadId] += nTime;
            if bDebugOutputGetUsageData: print "| %4X  %6s %s" % (uThreadId, nTime is None and "?" or ("+%.3f" % nTime), repr(sLine));
    if bDebugOutputGetUsageData: print "'".ljust(120, "-");
    oExcessiveCPUUsageDetector.ddnLastCPUTime_by_uThreadId_by_ProcessId = ddnCPUTime_by_uThreadId_by_uProcessId;
    oExcessiveCPUUsageDetector.nLastRunTime = oCdbWrapper.nApplicationRunTime;
