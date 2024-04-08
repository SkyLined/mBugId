import re, threading;

from mMultiThreading import cLock;

from .cBugReport import cBugReport;
from .dxConfig import dxConfig;
from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
# local imports are at the end of this file to avoid import loops.
from .mCP437 import fsCP437FromBytesString;

gbDebugOutput = False;
gbDebugOutputCalculation = False;
gbDebugOutputGetUsageData = False;
gbDebugOutputWorm = False;

grbThreadTimeHeader = re.compile(rb"^\s*Thread\s+Time\s*$");
grbTimeTypesHeader = re.compile(rb"^\s*(User Mode Time|Kernel Mode Time|Elapsed Time)\s*$");
grbThreadTime = re.compile(
  rb"^\s*"            #
  rb"\d+"             # index
  rb":"               # ":"
  rb"(\w+)"           # **thread-id**
  rb"\s+"             # whitespace
  rb"(\d+)"           # **days**
  rb"\s+days\s+"      # whitespace "days" whitespace
  rb"(\d\d?)"         # **hours**
  rb":"               # ":"
  rb"(\d\d)"          # **minutes**
  rb":"               # ":"
  rb"(\d\d\.\d\d\d)"  # **seconds "." milliseconds**
  rb"\s*$"            #
);

class cExcessiveCPUUsageDetector(object):
  def __init__(oSelf, oCdbWrapper):
    oSelf.oCdbWrapper = oCdbWrapper;
    oSelf.bStarted = False;
    oSelf.oLock = cLock(n0DeadlockTimeoutInSeconds = 1);
    oSelf.oCleanupTimeout = None;
    oSelf.oStartTimeout = None;
    oSelf.oCheckUsageTimeout = None;
    oSelf.oWormRunTimeout = None;
    oSelf.uWormBreakpointId = None;
    oSelf.uBugBreakpointId = None;
  
  def fStartTimeout(oSelf, nTimeoutInSeconds):
    if gbDebugOutput: print("@@@ Starting excessive CPU usage checks in %d seconds..." % nTimeoutInSeconds);
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
          f0Callback = oSelf.fCleanup,
        );
      if nTimeoutInSeconds is not None:
        oSelf.oStartTimeout = oCdbWrapper.foSetTimeout(
          sDescription = "Start excessive CPU Usage detector",
          nTimeoutInSeconds = nTimeoutInSeconds, 
          f0Callback = oSelf.fStart,
        );
    finally:
      oSelf.oLock.fRelease();
  
  def fCleanup(oSelf, oCdbWrapper):
    # Remove old breakpoints; this is done in a timeout because we cannot execute any command while the application
    # is still running.
    oSelf.oLock.fAcquire();
    try:
      if oSelf.oCleanupTimeout:
        oCdbWrapper.fClearTimeout(oSelf.oCleanupTimeout);
        oSelf.oCleanupTimeout = None;
        if gbDebugOutput: print("@@@ Cleaning up excessive CPU usage breakpoints...");
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
  
  def fStart(oSelf, oCdbWrapper):
    # A timeout to execute the cleanup function was set, but there is no guarantee the timeout has been fired yet; the
    # timeout to start this function may have been fired first. By calling the cleanup function now, we make sure that
    # cleanup happens if it has not already, and cancel the cleanup timeout if it has not yet fired.
    oSelf.bStarted = True;
    oSelf.fCleanup(oCdbWrapper);
    if gbDebugOutput: print("@@@ Start excessive CPU usage checks...");
    oSelf.fGetUsageData();
    oSelf.oLock.fAcquire();
    try:
      oSelf.oCheckUsageTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "Check CPU usage for excessive CPU Usage detector",
        nTimeoutInSeconds = dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"],
        f0Callback = oSelf.fCheckUsage,
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
    if gbDebugOutputCalculation:
      print(",--- cExcessiveCPUUsageDetector.fGetUsageData ".ljust(120, "-"));
      print("| Application run time: %.3f->%.3f=%.3f" % (nPreviousRunTimeInSeconds, nCurrentRunTimeInSeconds, nRunTimeInSeconds));
    uMaxCPUProcessId = None;
    for (uProcessId, dnCurrentCPUTimeInSeconds_by_uThreadId) in ddnCurrentCPUTimeInSeconds_by_uThreadId_by_uProcessId.items():
      if gbDebugOutputCalculation:
        print(("|--- Process 0x%X" % uProcessId).ljust(120, "-"));
        print("| %3s  %21s  %7s" % ("tid", "CPU time", "% Usage"));
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
        if gbDebugOutputCalculation:
          fsFormat = lambda nNumber: nNumber is None and " - " or ("%.3f" % nNumber);
          print("| %4X  %6s->%6s=%6s  %6s%%" % (
            uThreadId,
            fsFormat(nPreviousCPUTimeInSeconds), fsFormat(nCurrentCPUTimeInSeconds), fsFormat(nCPUTimeInSeconds),
            fsFormat(nCPUUsagePercent),
          ));
    if uMaxCPUProcessId is None:
      if gbDebugOutputCalculation:
        print("|".ljust(120, "-"));
        print("| Insufficient data");
        print("'".ljust(120, "-"));
      return None, None, None, None;
    if gbDebugOutputCalculation:
      print("|".ljust(120, "-"));
      print("| Total CPU usage: %d%%, max: %d%% for pid 0x%X, tid 0x%X" % \
         (nTotalCPUUsagePercent, nMaxCPUUsagePercent, uMaxCPUProcessId, uMaxCPUThreadId));
      print("'".ljust(120, "-"));
    elif gbDebugOutput:
      print("*** Total CPU usage: %d%%, max: %d%% for pid %d, tid %d" % \
          (nTotalCPUUsagePercent, nMaxCPUUsagePercent, uMaxCPUProcessId, uMaxCPUThreadId));
    # Rounding errors can give results > 100%. Fix that.
    if nTotalCPUUsagePercent > 100:
      nTotalCPUUsagePercent = 100.0;
    return uMaxCPUProcessId, uMaxCPUThreadId, nMaxCPUTimeInSeconds, nTotalCPUUsagePercent;
  
  def fCheckForExcessiveCPUUsage(oSelf, fCallback):
    if gbDebugOutput: print("@@@ Checking for excessive CPU usage...");
    # We need to gather CPU Usage data now, wait nIntervalInSeconds and get it again to see if any thread is
    # currently using a lot of CPU:
    oSelf.fGetUsageData();
    def fExcessiveCPUUsageCheckIntervalTimeoutHandler(oCdbWrapper): # Called after the nIntervalInSeconds timeout fires.
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
      f0Callback = fExcessiveCPUUsageCheckIntervalTimeoutHandler,
    );
  
  def fCheckUsage(oSelf, oCdbWrapper):
    if gbDebugOutput: print("@@@ Checking for excessive CPU usage...");
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
          f0Callback = oSelf.fCheckUsage,
        );
    finally:
      oSelf.oLock.fRelease();
  
  def fWormDebugOutput(oSelf, sbMessage, *auArguments):
    oCdbWrapper = oSelf.oCdbWrapper;
    asbDebugOutput = oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = b'.printf "CPUUsage worm: %s\\r\\n"%s;' % \
          (sbMessage, b"".join([b", 0x%X" % uArgument for uArgument in auArguments])),
      sb0Comment = None,
      bShowOutputButNotCommandInHTMLReport = True,
    );
    assert len(asbDebugOutput) == 1, "Unexpected output: %s" % repr(asbDebugOutput);
    if gbDebugOutputWorm: print("@@@ %3.3f %s" % (oCdbWrapper.nApplicationRunTimeInSeconds, asbDebugOutput[0]));
  
  def fInstallWorm(oSelf, uProcessId, uThreadId, nTotalCPUUsagePercent):
    assert oSelf.oLock.bLocked, \
        "This method can only be called when the lock is acquired";
    if gbDebugOutput: print("@@@ Installing excessive CPU usage worm...");
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
    oCdbWrapper.fSelectProcessIdAndThreadId(uProcessId, uThreadId);
    oWormProcess = oCdbWrapper.oCdbCurrentProcess;
    oWormWindowsAPIThread = oCdbWrapper.oCdbCurrentWindowsAPIThread;
    oSelf.uProcessId = uProcessId;
    oSelf.uThreadId = uThreadId;
    oSelf.nTotalCPUUsagePercent = nTotalCPUUsagePercent;
    u0InstructionPointer = oWormWindowsAPIThread.fu0GetRegister(b"*ip");
    u0StackPointer = oWormWindowsAPIThread.fu0GetRegister(b"*sp");
    # Perhaps some graceful handling may be in order if this happens often but I do not expect it to
    assert u0InstructionPointer is not None and u0StackPointer is not None, \
        "Cannot get Instruction and/or Stack Pointer";
    uInstructionPointer = u0InstructionPointer;
    uStackPointer = u0StackPointer;
# Ideally, we'de use the return address here but for some unknown reason cdb may not give a valid value at this point.
# However, we can use the instruction pointer to set our first breakpoint and when it is hit, the return address will be
# correct... sigh.
#    uReturnAddress = oSelf.oWormProcess.fuGetValueForRegister(b"$ra", b"Get return address");
    uBreakpointAddress = uInstructionPointer; # uReturnAddress would be preferred.
    oSelf.fWormDebugOutput(
      b"Starting at IP=%p by creating a breakpoint at IP=%p, SP=%p...",
      uInstructionPointer, uBreakpointAddress, uStackPointer
    );
    oSelf.uLastInstructionPointer = uInstructionPointer;
    oSelf.uLastStackPointer = uStackPointer;
    oSelf.uNextBreakpointAddress = uBreakpointAddress;
    oSelf.uWormBreakpointId = oCdbWrapper.fuAddBreakpointForProcessIdAndAddress(
      uProcessId = oSelf.uProcessId,
      uAddress = uBreakpointAddress,
      fCallback = lambda uBreakpointId: oSelf.fMoveWormBreakpointUpTheStack(),
      u0ThreadId = oSelf.uThreadId,
    );
    assert oSelf.uWormBreakpointId is not None, \
        "Could not create breakpoint at 0x%X" % oSelf.uLastInstructionPointer;
    oSelf.oWormRunTimeout = oCdbWrapper.foSetTimeout(
        sDescription = "Start worm for excessive CPU Usage detector",
        nTimeoutInSeconds = dxConfig["nExcessiveCPUUsageWormRunTimeInSeconds"],
        f0Callback = oSelf.fSetBugBreakpointAfterTimeout,
    );
  
  def fMoveWormBreakpointUpTheStack(oSelf):
    oCdbWrapper = oSelf.oCdbWrapper;
    oSelf.oLock.fAcquire();
    try:
      oCdbWrapper.fSelectProcessIdAndThreadId(oSelf.uProcessId, oSelf.uThreadId);
      oWormProcess = oCdbWrapper.oCdbCurrentProcess;
      oWormWindowsAPIThread = oCdbWrapper.oCdbCurrentWindowsAPIThread;
      u0InstructionPointer = oWormWindowsAPIThread.fu0GetRegister(b"*ip");
      u0StackPointer = oWormWindowsAPIThread.fu0GetRegister(b"*sp");
      # Perhaps some graceful handling may be in order if this happens often but I do not expect it to.
      assert u0InstructionPointer is not None and u0StackPointer is not None, \
          "Cannot get Instruction and/or Stack Pointer";
      uInstructionPointer = u0InstructionPointer;
      uStackPointer = u0StackPointer;
      # This is a sanity check: the instruction pointer should point to the instruction (or after the int3 instruction
      # inserted by cdb) where the breakpoint was set.
      assert uInstructionPointer in [oSelf.uNextBreakpointAddress, oSelf.uNextBreakpointAddress + 1], \
          "Expected to hit breakpoint at 0x%X, but got 0x%X instead !?" % \
          (oSelf.uNextBreakpointAddress, uInstructionPointer);
      # The code we're expecting to return to may actually be *called* in recursive code. We can detect this by checking
      # if the stack pointer has increased or not. If not, we have not yet returned and will ignore this breakpoint.
      if uStackPointer <= oSelf.uLastStackPointer:
        oSelf.fWormDebugOutput(
          b"Ignored breakpoint at IP=%p, SP=%p: SP but must be >%p",
          uInstructionPointer, uStackPointer, oSelf.uLastStackPointer
        );
        return;
      uReturnAddress = oWormProcess.fuGetValueForRegister(b"$ra", b"Get return address");
      if oSelf.uNextBreakpointAddress == uReturnAddress:
        oSelf.fWormDebugOutput(
          b"Moving from IP=%p, SP=%p to IP=%p, SP=%p, by leaving breakpoint in place and adjusting expected SP...",
          uInstructionPointer, oSelf.uLastStackPointer, uReturnAddress, uStackPointer
        );
        # This is a recursive call, the breakpoint does not need to be moved.
        oSelf.uLastStackPointer = uStackPointer;
      else:
        oSelf.fWormDebugOutput(
          b"Moving from IP=%p, SP=%p to IP=%p, SP=%p, by creating a new breakpoint...",
          uInstructionPointer, oSelf.uLastStackPointer, uReturnAddress, uStackPointer,
        );
        # Try to move the breakpoint to the return address:
        uNewWormBreakpointId = oCdbWrapper.fuAddBreakpointForProcessIdAndAddress(
          uProcessId = oSelf.uProcessId,
          uAddress = uReturnAddress,
          fCallback = lambda uBreakpointId: oSelf.fMoveWormBreakpointUpTheStack(),
          u0ThreadId = oSelf.uThreadId,
        );
        if uNewWormBreakpointId is None:
          # Could not move breakpoint: the return address may be invalid.
          # Ignore this and continue to run; the unchanged breakpoint may get hit again and we get another try, or
          # the timeout fires and we get a stack.
          oSelf.fWormDebugOutput(
            b"Unable to create breakpoint at IP=%p: worm breakpoint remains at IP=%p, SP=%p...",
            uReturnAddress, uInstructionPointer, oSelf.uLastStackPointer,
          );
        else:
          oSelf.fWormDebugOutput(
            b"Removing old breakpoint at IP=%p, SP=%p...",
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
        f0Callback = oSelf.fSetBugBreakpointAfterTimeout,
      );
    finally:
      oSelf.oLock.fRelease();

  def fSetBugBreakpointAfterTimeout(oSelf, oCdbWrapper):
    # Ideally, we'd check here to make sure the application has actually been using CPU for
    # dxConfig["nExcessiveCPUUsageWormRunTimeInSeconds"] seconds since the last breakpoint was hit: if there were many
    # breakpoints, this will not be the case. Doing so should improve the reliability of the result.
    oCdbWrapper = oSelf.oCdbWrapper;
    if gbDebugOutput: print("@@@ Worm run timeout: setting excessive CPU usage bug breakpoint...");
    oSelf.oLock.fAcquire();
    try:
      if oSelf.oWormRunTimeout is None:
        return; # Analysis was stopped because a new timeout was set.
      oSelf.oWormRunTimeout = None;
      oSelf.fWormDebugOutput(
        b"Run timeout; stopping worm and creating bug breakpoint...",
      );
      # Remove worm breakpoint
      oSelf.fWormDebugOutput(
        b"Removing old worm breakpoint at IP=%p, SP=%p...",
        oSelf.uLastInstructionPointer, oSelf.uLastStackPointer,
      );
      oCdbWrapper.fRemoveBreakpoint(oSelf.uWormBreakpointId);
      oSelf.uWormBreakpointId = None;
      # Set bug breakpoint
      oSelf.fWormDebugOutput(
        b"Creating bug breakpoint at IP=%p, SP=%p...",
        oSelf.uLastInstructionPointer, oSelf.uLastStackPointer
      );
      oSelf.uBugBreakpointId = oCdbWrapper.fuAddBreakpointForProcessIdAndAddress(
        uProcessId = oSelf.uProcessId,
        uAddress = oSelf.uLastInstructionPointer,
        fCallback = lambda uBreakpointId: oSelf.fReportCPUUsageBug(),
        u0ThreadId = oSelf.uThreadId,
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
      oCdbWrapper.fSelectProcessIdAndThreadId(oSelf.uProcessId, oSelf.uThreadId);
      oWormProcess = oCdbWrapper.oCdbCurrentProcess;
      oWormWindowsAPIThread = oCdbWrapper.oCdbCurrentWindowsAPIThread;
      u0InstructionPointer = oWormWindowsAPIThread.fu0GetRegister(b"*ip");
      u0StackPointer = oWormWindowsAPIThread.fu0GetRegister(b"*sp");
      # Perhaps some graceful handling may be in order if this happens often but I do not expect it to.
      assert u0InstructionPointer is not None and u0StackPointer is not None, \
          "Cannot get Instruction and/or Stack Pointer";
      uInstructionPointer = u0InstructionPointer;
      uStackPointer = u0StackPointer;
      # This is a sanity check: the instruction pointer should point to the instruction (or after the int3 instruction
      # inserted by cdb) where the breakpoint was set.
      assert uInstructionPointer in [oSelf.uNextBreakpointAddress, oSelf.uNextBreakpointAddress + 1], \
          "Expected to hit breakpoint at 0x%X, but got 0x%X instead !?" % \
          (oSelf.uNextBreakpointAddress, uInstructionPointer);
      # The code we're expecting to return to may actually be *called* in recursive code. We can detect this by checking
      # if the stack pointer has increased or not. If not, we have not yet returned and will ignore this breakpoint.
      if uStackPointer < oSelf.uLastStackPointer:
        oSelf.fWormDebugOutput(
          b"Ignored bug breakpoint at IP=%p, SP=%p: SP but must be >=%p",
          uInstructionPointer, uStackPointer, oSelf.uLastStackPointer
        );
        return;
      if gbDebugOutput: print("@@@ Reporting excessive CPU usage bug...");
      oSelf.fWormDebugOutput(
        b"Bug breakpoint at IP=%p, SP=%p is hit, removing breakpoint and reporting bug...",
        uInstructionPointer, uStackPointer,
      );
      # Remove the breakpoint
      oCdbWrapper.fRemoveBreakpoint(oSelf.uBugBreakpointId);
      oSelf.uBugBreakpointId = None;
      # Report a bug
      sBugDescription = "The application was using %d%% CPU for %d seconds, which is considered excessive." % \
          (oSelf.nTotalCPUUsagePercent, dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"]);
      oBugReport = cBugReport.foCreate(
        oCdbWrapper = oCdbWrapper,
        oProcess = oWormProcess,
        oWindowsAPIThread = oWormWindowsAPIThread,
        o0Exception = None,
        s0BugTypeId = "CPUUsage",
        s0BugDescription = sBugDescription,
        s0SecurityImpact = None,
      );
      oBugReport.bRegistersRelevant = False;
      oBugReport.fReport();
      oCdbWrapper.fStop();
    finally:
      oSelf.oLock.fRelease();
  
  def fGetUsageData(oSelf):
    oCdbWrapper = oSelf.oCdbWrapper;
    # Get the amount of CPU time each thread in each process has consumed
    ddnCPUTimeInSeconds_by_uThreadId_by_uProcessId = {};
    sb0TimeType = None;
    if gbDebugOutputGetUsageData:
      print(",--- cExcessiveCPUUsageDetector.fGetUsageData ".ljust(120, "-"));
    for uProcessId in oCdbWrapper.doProcess_by_uId.keys():
      if gbDebugOutputGetUsageData:
        print(("|--- Process 0x%X" % uProcessId).ljust(120, "-"));
        print("| %4s  %6s  %s" % ("tid", "time", "source line"));
      oCdbWrapper.fSelectProcessId(uProcessId);
      asbThreadTimes = oCdbWrapper.fasbExecuteCdbCommand(
        sbCommand = b"!runaway 7;",
        sb0Comment = b"Get CPU usage information",
      );
      dnCPUTimeInSeconds_by_uThreadId = {};
      dnCPUTimeInSeconds_by_uThreadId = ddnCPUTimeInSeconds_by_uThreadId_by_uProcessId[uProcessId] = {};
      for sbLine in asbThreadTimes:
        if grbThreadTimeHeader.match(sbLine):
          pass; # Header, ignored.
        elif grbTimeTypesHeader.match(sbLine):
          sb0TimeType = sbLine.strip(); # Keep track of what type of type of times are being reported.
        else:
          assert sb0TimeType is not None, \
              "Expected a header before values in %s.\r\n%s" % \
              (sbLine, "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbThreadTimes));
          obThreadTimeMatch = grbThreadTime.match(sbLine);
          assert obThreadTimeMatch, \
              "Unrecognized \"!runaway3\" output: %s\r\n%s" % \
              (sbLine, "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbThreadTimes));
          (sbThreadId, sbDays, sbHours, sbMinutes, sbSecondsMilliseconds) = \
            obThreadTimeMatch.groups();
          uThreadId = fu0ValueFromCdbHexOutput(sbThreadId);
          nTimeInSeconds = ((int(sbDays) * 24 + int(sbHours)) * 60 + int(sbMinutes)) * 60 + float(sbSecondsMilliseconds);
          if nTimeInSeconds >= 2000000000:
            # Due to a bug in !runaway, elapsed time sometimes gets reported as a very, very large number.
            assert sb0TimeType == b"Elapsed Time", \
                "Unexpected large value for %s: %s\r\n%s" % (
                  sb0TimeType,
                  nTimeInSeconds,
                  "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbThreadTimes)
                );
            # In such cases, do not return a value for elapsed time.
            nTimeInSeconds = None;
          if sb0TimeType == b"User Mode Time":
            dnCPUTimeInSeconds_by_uThreadId[uThreadId] = nTimeInSeconds;
            if gbDebugOutputGetUsageData: print("| %4X  %6s %s" % (uThreadId, nTimeInSeconds is None and "?" or ("%.3f" % nTimeInSeconds), repr(sbLine)));
          elif sb0TimeType == b"Kernel Mode Time":
            dnCPUTimeInSeconds_by_uThreadId[uThreadId] += nTimeInSeconds;
            if gbDebugOutputGetUsageData: print("| %4X  %6s %s" % (uThreadId, nTimeInSeconds is None and "?" or ("+%.3f" % nTimeInSeconds), repr(sbLine)));
    if gbDebugOutputGetUsageData: print("'".ljust(120, "-"));
    oSelf.ddnLastCPUTimeInSeconds_by_uThreadId_by_ProcessId = ddnCPUTimeInSeconds_by_uThreadId_by_uProcessId;
    oSelf.nLastRunTimeInSeconds = oCdbWrapper.nApplicationRunTimeInSeconds;
