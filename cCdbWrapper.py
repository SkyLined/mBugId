import itertools, re, subprocess, sys, threading, time;
from cCdbWrapper_fasGetStack import cCdbWrapper_fasGetStack;
from cCdbWrapper_fasReadOutput import cCdbWrapper_fasReadOutput;
from cCdbWrapper_fasSendCommandAndReadOutput import cCdbWrapper_fasSendCommandAndReadOutput;
from cCdbWrapper_fauGetBytes import cCdbWrapper_fauGetBytes;
from cCdbWrapper_fCdbCleanupThread import cCdbWrapper_fCdbCleanupThread;
from cCdbWrapper_fCdbInterruptOnTimeoutThread import cCdbWrapper_fCdbInterruptOnTimeoutThread;
from cCdbWrapper_fCdbStdErrThread import cCdbWrapper_fCdbStdErrThread;
from cCdbWrapper_fCdbStdInOutThread import cCdbWrapper_fCdbStdInOutThread;
from cCdbWrapper_fsHTMLEncode import cCdbWrapper_fsHTMLEncode;
from cCdbWrapper_fuGetValue import cCdbWrapper_fuGetValue;
from cCdbWrapper_fuGetValueForSymbol import cCdbWrapper_fuGetValueForSymbol;
from cCdbWrapper_f_Timeout import cCdbWrapper_fxSetTimeout, cCdbWrapper_fClearTimeout;
from cCdbWrapper_f_Breakpoint import cCdbWrapper_fuAddBreakpoint, cCdbWrapper_fRemoveBreakpoint;
from cCdbWrapper_fsGetSymbolForAddress import cCdbWrapper_fsGetSymbolForAddress;
from cCdbWrapper_fsGetUnicodeString import cCdbWrapper_fsGetUnicodeString;
from cExcessiveCPUUsageDetector import cExcessiveCPUUsageDetector;
from dxConfig import dxConfig;
from Kill import fKillProcessesUntilTheyAreDead;
from sOSISA import sOSISA;

class cCdbWrapper(object):
  def __init__(oCdbWrapper,
    sCdbISA,                                  # Which version of cdb should be used to debug this application? ("x86" or "x64")
    asApplicationCommandLine,
    auApplicationProcessIds,
    asLocalSymbolPaths,
    asSymbolCachePaths, 
    asSymbolServerURLs,
    dsURLTemplate_by_srSourceFilePath,
    rImportantStdOutLines,
    rImportantStdErrLines,
    bGenerateReportHTML,        
    fFailedToDebugApplicationCallback,        # called when the application cannot be started by the debugger, or the
                                              # debugger cannot attach to the given process ids. Arguments:
                                              # (oBugId, sErrorMessage).
    fApplicationRunningCallback,              # called when the application is started in the debugger, or the
                                              # processes the debugger attached to have been resumed.
    fApplicationSuspendedCallback,            # called when the application is suspended to handle an exception,
                                              # timeout or breakpoint.
    fApplicationResumedCallback,              # called after the application was suspended, right before the
                                              # application is resumed again.
    fMainProcessTerminatedCallback,           # called when (any of) the application's "main" processes terminate.
                                              # When BugId starts an application, the first process created is the main
                                              # process. When BugId to attaches to one or more processes, these are the
                                              # main processes. This callback is not called when any child processes
                                              # spawned by these main processes terminate.
    fInternalExceptionCallback,               # called when there is a bug in BugId itself.
    fFinishedCallback,                        # called when BugId is finished.
    fPageHeapNotEnabledCallback,              # called when page heap is not enabled for a particular binary.
    fStdErrOutputCallback,                    # called whenever there is output on stderr
    fNewProcessCallback,                      # called whenever there is a new process.
  ):
    oCdbWrapper.sCdbISA = sCdbISA or sOSISA;
    oCdbWrapper.asApplicationCommandLine = asApplicationCommandLine;
    oCdbWrapper.dsURLTemplate_by_srSourceFilePath = dsURLTemplate_by_srSourceFilePath or {};
    oCdbWrapper.rImportantStdOutLines = rImportantStdOutLines;
    oCdbWrapper.rImportantStdErrLines = rImportantStdErrLines;
    oCdbWrapper.bGenerateReportHTML = bGenerateReportHTML;
    oCdbWrapper.fFailedToDebugApplicationCallback = fFailedToDebugApplicationCallback;
    oCdbWrapper.fApplicationRunningCallback = fApplicationRunningCallback;
    oCdbWrapper.fApplicationSuspendedCallback = fApplicationSuspendedCallback;
    oCdbWrapper.fApplicationResumedCallback = fApplicationResumedCallback;
    oCdbWrapper.fMainProcessTerminatedCallback = fMainProcessTerminatedCallback;
    oCdbWrapper.fInternalExceptionCallback = fInternalExceptionCallback;
    oCdbWrapper.fFinishedCallback = fFinishedCallback;
    oCdbWrapper.fPageHeapNotEnabledCallback = fPageHeapNotEnabledCallback;
    oCdbWrapper.fStdErrOutputCallback = fStdErrOutputCallback;
    oCdbWrapper.fNewProcessCallback = fNewProcessCallback;
    oCdbWrapper.oExtension = None; # The debugger extension is not loaded (yet).
    uSymbolOptions = sum([
      0x00000001, # SYMOPT_CASE_INSENSITIVE
      0x00000002, # SYMOPT_UNDNAME
      0x00000004 * (dxConfig["bDeferredSymbolLoads"] and 1 or 0), # SYMOPT_DEFERRED_LOAD
#     0x00000008, # SYMOPT_NO_CPP
      0x00000010 * (dxConfig["bEnableSourceCodeSupport"] and 1 or 0), # SYMOPT_LOAD_LINES
#     0x00000020, # SYMOPT_OMAP_FIND_NEAREST
#     0x00000040, # SYMOPT_LOAD_ANYTHING
#     0x00000080, # SYMOPT_IGNORE_CVREC
      0x00000100 * (not dxConfig["bDeferredSymbolLoads"] and 1 or 0), # SYMOPT_NO_UNQUALIFIED_LOADS
      0x00000200, # SYMOPT_FAIL_CRITICAL_ERRORS
#     0x00000400, # SYMOPT_EXACT_SYMBOLS
      0x00000800, # SYMOPT_ALLOW_ABSOLUTE_SYMBOLS
      0x00001000 * (not dxConfig["bUse_NT_SYMBOL_PATH"] and 1 or 0), # SYMOPT_IGNORE_NT_SYMPATH
      0x00002000, # SYMOPT_INCLUDE_32BIT_MODULES 
#     0x00004000, # SYMOPT_PUBLICS_ONLY
#     0x00008000, # SYMOPT_NO_PUBLICS
      0x00010000, # SYMOPT_AUTO_PUBLICS
      0x00020000, # SYMOPT_NO_IMAGE_SEARCH
#     0x00040000, # SYMOPT_SECURE
      0x00080000, # SYMOPT_NO_PROMPTS
#     0x80000000, # SYMOPT_DEBUG (don't set here: will be switched on and off later as needed)
    ]);
    # Get the cdb binary path
    sCdbBinaryPath = dxConfig["sCdbBinaryPath_%s" % oCdbWrapper.sCdbISA];
    assert sCdbBinaryPath, "No %s cdb binary path found" % oCdbWrapper.sCdbISA;
    # Get the command line (without starting/attaching to a process)
    asCommandLine = [
      sCdbBinaryPath,
      "-o", # Debug any child processes spawned by the main processes as well.

      "-sflags", "0x%08X" % uSymbolOptions # Set symbol loading options (See above for details)
    ];
    if dxConfig["bEnableSourceCodeSupport"]:
      asCommandLine += ["-lines"];
    # Get a list of symbol paths, caches and servers to use:
    asLocalSymbolPaths = asLocalSymbolPaths or [];
    if asSymbolCachePaths is None:
      asSymbolCachePaths = dxConfig["asDefaultSymbolCachePaths"];
    # If not symbols should be used, or no symbol paths are provided, don't use them:
    if asSymbolServerURLs is None:
      asSymbolServerURLs = dxConfig["asDefaultSymbolServerURLs"];
    oCdbWrapper.bUsingSymbolServers = asSymbolServerURLs;
    # Construct the cdb symbol path if one is needed and add it as an argument.
    sSymbolsPath = ";".join(asLocalSymbolPaths + ["cache*%s" % x for x in asSymbolCachePaths] + ["srv*%s" % x for x in asSymbolServerURLs]);
    if sSymbolsPath:
      asCommandLine += ["-y", sSymbolsPath];
    oCdbWrapper.doProcess_by_uId = {};
    oCdbWrapper.oCurrentProcess = None; # The current process id in cdb's context
    oCdbWrapper.auProcessIdsPendingAttach = auApplicationProcessIds or [];
    oCdbWrapper.auProcessIdsPendingDelete = []; # There should only ever be one in this list, but that is not enforced.
    # Keep track of what the applications "main" processes are.
    oCdbWrapper.aoMainProcesses = [];
    if asApplicationCommandLine is not None:
      # If a process must be started, add it to the command line.
      assert not auApplicationProcessIds, "Cannot start a process and attach to processes at the same time";
      asCommandLine += asApplicationCommandLine;
    else:
      assert auApplicationProcessIds, "Must start a process or attach to one";
      # If any processes must be attached to, add the first to the coommand line.
      asCommandLine += ["-p", str(auApplicationProcessIds[0])];
    # Quote any non-quoted argument that contain spaces:
    asCommandLine = [
      (x and (x[0] == '"' or x.find(" ") == -1)) and x or '"%s"' % x.replace('"', '\\"')
      for x in asCommandLine
    ];
    # Show the command line if requested.
    if dxConfig["bOutputCommandLine"]:
      print "* Starting %s" % " ".join(asCommandLine);
    # Initialize some variables
    oCdbWrapper.sCurrentISA = None; # During exception handling, this is set to the ISA for the code that caused it.
    if bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML = ""; # Logs stdin/stdout/stderr for the cdb process, grouped by executed command.
      oCdbWrapper.sPromptHTML = None; # Logs cdb prompt to be adde to CdbIOHTML if a command is added.
    oCdbWrapper.oBugReport = None; # Set to a bug report if a bug was detected in the application
    oCdbWrapper.bCdbRunning = True; # Set to False after cdb terminated, used to terminate the debugger thread.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = False; # Set to True when cdb is terminated on purpose, used to detect unexpected termination.
    if bGenerateReportHTML:
      oCdbWrapper.sImportantOutputHTML = ""; # Lines from stdout/stderr that are marked as potentially important to understanding the bug.
    # cdb variables are in short supply, so a mechanism must be used to allocate and release them.
    # See fuGetVariableId and fReleaseVariableId for implementation details.
    oCdbWrapper.uAvailableVariableIds = list(xrange(20)); # $t0-$t19. 
    # To make it easier to refer to cdb breakpoints by id, a mechanism must be used to allocate and release them
    # See fuGetBreakpointId and fReleaseBreakpointId for implementation details.
    oCdbWrapper.oBreakpointCounter = itertools.count(); # None have been used so far, so start at 0.
    # You can set a breakpoint that results in a bug being reported when it is hit.
    # See fuAddBugBreakpoint and fReleaseBreakpointId for implementation details.
    oCdbWrapper.duAddress_by_uBreakpointId = {};
    oCdbWrapper.duProcessId_by_uBreakpointId = {};
    oCdbWrapper.dfCallback_by_uBreakpointId = {};
    # You can tell BugId to check for excessive CPU usage among all the threads running in the application.
    # See fSetCheckForExcessiveCPUUsageTimeout and cExcessiveCPUUsageDetector.py for more information
    oCdbWrapper.oExcessiveCPUUsageDetector = cExcessiveCPUUsageDetector(oCdbWrapper);
    # Keep track of future timeouts and their callbacks
    oCdbWrapper.axTimeouts = [];
    oCdbWrapper.oTimeoutsLock = threading.Lock();
    # incremented whenever a CTRL+BREAK event is sent to cdb by the interrupt-on-timeout thread, so the stdio thread
    # knows to expect a DBG_CONTROL_BREAK exception and won't report it as an error.
    oCdbWrapper.uCdbBreakExceptionsPending = 0;
    # oCdbLock is used by oCdbStdInOutThread and oCdbInterruptOnTimeoutThread to allow the former to execute commands
    # (other than "g") without the later attempting to get cdb to suspend the application with a breakpoint, and vice
    # versa. It's acquired on behalf of the former, to prevent the later from interrupting before the application has
    # even started.
    oCdbWrapper.oCdbLock = threading.Lock();
    oCdbWrapper.oCdbLock.acquire();
    oCdbWrapper.bCdbStdInOutThreadRunning = True; # Will be set to false if the thread terminates for any reason.
    # Keep track of how long the application has been running, used for timeouts (see fxSetTimeout, fCdbStdInOutThread
    # and fCdbInterruptOnTimeoutThread for details. The debugger can tell is what time it thinks it is before we start
    # and resume the application as well as what time it thinks it was when an exception happened. The difference is
    # used to calculate how long the application has been running. We cannot simply use time.clock() before start/
    # resuming and at the time an event is handled as the debugger may take quite some time processing an event before
    # we can call time.clock(): this time would incorrectly be added to the time the application has spent running.
    # However, while the application is running, we cannot ask the debugger what time it thinks it is, so we have to 
    # rely on time.clock(). Hence, both values are tracked.
    oCdbWrapper.oApplicationTimeLock = threading.Lock();
    oCdbWrapper.nApplicationRunTime = 0; # Total time spent running before last interruption
    oCdbWrapper.nApplicationResumeDebuggerTime = None;  # debugger time at the moment the application was last resumed
    oCdbWrapper.nApplicationResumeTime = None;          # time.clock() at the moment the application was last resumed
    oCdbWrapper.oCdbProcess = subprocess.Popen(
      args = " ".join(asCommandLine),
      stdin = subprocess.PIPE,
      stdout = subprocess.PIPE,
      stderr = subprocess.PIPE,
      creationflags = subprocess.CREATE_NEW_PROCESS_GROUP,
    );
    
    # Create a thread that interacts with the debugger to debug the application
    oCdbWrapper.oCdbStdInOutThread = oCdbWrapper._foThread(cCdbWrapper_fCdbStdInOutThread);
    # Create a thread that reads stderr output and shows it in the console
    oCdbWrapper.oCdbStdErrThread = oCdbWrapper._foThread(cCdbWrapper_fCdbStdErrThread);
    # Create a thread that checks for a timeout to interrupt cdb when needed.
    oCdbWrapper.oCdbInterruptOnTimeoutThread = oCdbWrapper._foThread(cCdbWrapper_fCdbInterruptOnTimeoutThread);
    # Create a thread that waits for the debugger to terminate and cleans up after it.
    oCdbWrapper.oCdbCleanupThread = oCdbWrapper._foThread(cCdbWrapper_fCdbCleanupThread);
  
  def fStart(oCdbWrapper):
    oCdbWrapper.oCdbStdInOutThread.start();
    oCdbWrapper.oCdbStdErrThread.start();
    oCdbWrapper.oCdbInterruptOnTimeoutThread.start();
    oCdbWrapper.oCdbCleanupThread.start();
  
  def _foThread(oCdbWrapper, fActivity):
    return threading.Thread(target = oCdbWrapper._fThreadWrapper, args = (fActivity,));
  
  def _fThreadWrapper(oCdbWrapper, fActivity):
    try:
      fActivity(oCdbWrapper);
    except Exception, oException:
      cException, oException, oTraceBack = sys.exc_info();
      try:
        oCdbWrapper.fInternalExceptionCallback(oException, oTraceBack);
      finally:
        oCdbProcess = getattr(oCdbWrapper, "oCdbProcess", None);
        if not oCdbProcess:
          oCdbWrapper.bCdbRunning = False;
          return;
        if oCdbProcess.poll() is not None:
          oCdbWrapper.bCdbRunning = False;
          return;
        oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
        # cdb is still running: try to terminate cdb the normal way.
        try:
          oCdbProcess.terminate();
        except:
          pass;
        else:
          oCdbWrapper.bCdbRunning = False;
          return;
        if oCdbProcess.poll() is not None:
          oCdbWrapper.bCdbRunning = False;
          return;
        # cdb is still running: try to terminate cdb the hard way.
        fKillProcessesUntilTheyAreDead([oCdbProcess.pid]);
        # Make sure cdb finally died.
        assert oCdbProcess.poll() is not None, \
            "cdb did not die after killing it repeatedly";
        oCdbWrapper.bCdbRunning = False;
        return;
  
  def fStop(oCdbWrapper):
    oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
    oCdbProcess = getattr(oCdbWrapper, "oCdbProcess", None);
    if oCdbProcess:
      try:
        oCdbProcess.terminate();
      except:
        pass;
    # The below three threads may have called an event callback, which issued this fStop call. Therefore, we cannot
    # wait for them to terminate, as this could mean "waiting until we stop waiting", which takes forever. Since Python
    # won't allow you to wait for yourself, this could thow a RuntimeError exception: "cannot join current thread".
    # oCdbWrapper.oCdbStdInOutThread.join();
    # oCdbWrapper.oCdbStdErrThread.join();
    # oCdbWrapper.oCdbCleanupThread.join();
    # However, this should not be a problem. The first two thread stop running as soon as they notice cdb has
    # terminated. This functions waits for that as well, so the threads should stop at the same time or soon after this
    # function returns. This is assuming they have not called a callback that does not return: that is a bug, but not
    # in BugIg, but in that callback function. The third thread waits for the first two, does some cleanup and then
    # stops running as well. In other words, termination is guaranteed assuming any active callbacks do not block.
      oCdbProcess.wait();
    oCdbWrapper.bCdbRunning = False;
  
  def __del__(oCdbWrapper):
    # Check to make sure the debugger process is not running
    oCdbProcess = getattr(oCdbWrapper, "oCdbProcess", None);
    if oCdbProcess and oCdbProcess.poll() is None:
      print "*** INTERNAL ERROR: cCdbWrapper did not terminate, the cdb process is still running.";
      oCdbProcess.terminate();
  
  def fuGetVariableId(oCdbWrapper):
    return oCdbWrapper.uAvailableVariableIds.pop();
  def fReleaseVariableId(oCdbWrapper, uVariableId):
    oCdbWrapper.uAvailableVariableIds.append(uVariableId);
  
  # Select process/thread
  def fSelectProcess(oCdbWrapper, uProcessId):
    return oCdbWrapper.fSelectProcessAndThread(uProcessId = uProcessId);
  def fSelectThread(oCdbWrapper, uThreadId):
    return oCdbWrapper.fSelectProcessAndThread(uThreadId = uThreadId);
  def fSelectProcessAndThread(oCdbWrapper, uProcessId = None, uThreadId = None):
    # Both arguments are optional
    sSelectCommand = "";
    asSelected = [];
    if uProcessId is not None and uProcessId != oCdbWrapper.oCurrentProcess.uId:
      # Select process if it is not yet the current process.
      assert uProcessId in oCdbWrapper.doProcess_by_uId, \
          "Unknown process id %d/0x%X" % (uProcessId, uProcessId);
      sSelectCommand += "|~[0x%X]s;" % uProcessId;
      asSelected.append("process");
      # Assuming there's no error, track the new current process.
      oCdbWrapper.oCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
      if oCdbWrapper.oCurrentProcess.sISA != oCdbWrapper.sCurrentISA:
        # Select process ISA if it is not yet the current ISA. ".block{}" is required
        sSelectCommand += ".block{.effmach %s;};" % {"x86": "x86", "x64": "amd64"}[oCdbWrapper.oCurrentProcess.sISA];
        # Assuming there's no error, track the new current isa.
        oCdbWrapper.sCurrentISA = oCdbWrapper.oCurrentProcess.sISA;
        asSelected.append("isa");
    if uThreadId is not None:
      # We're not tracking the current thread; always set this.
      # TODO: track the current thread to reduce the number of times we may need to execute this command:
      sSelectCommand += "~~[0x%X]s;" % uThreadId;
      asSelected.append("thread");
    if sSelectCommand:
      # We need to select a different process, isa or thread in cdb.
      sSelectCommand += " $$ Select %s" % "/".join(asSelected); # Add a comment.
      asSelectCommandOutput = oCdbWrapper.fasSendCommandAndReadOutput(sSelectCommand);
      if "isa" in asSelected:
        bUnexpectedOutput = len(asSelectCommandOutput) != 1 or asSelectCommandOutput[0] not in [
          "Effective machine: x86 compatible (x86)",
          "Effective machine: x64 (AMD64)"
        ];
      else:
        bUnxepectedOutput = len(asSelectCommandOutput) != 0;
      assert not bUnxepectedOutput, \
          "Unexpected select %s output:\r\n%s" % ("/".join(asSelected), "\r\n".join(asSelectCommandOutput));
  
  # Excessive CPU usage
  def fSetCheckForExcessiveCPUUsageTimeout(oCdbWrapper, nTimeout):
    oCdbWrapper.oExcessiveCPUUsageDetector.fStartTimeout(nTimeout);
  
  def fnApplicationRunTime(oCdbWrapper):
    oCdbWrapper.oApplicationTimeLock.acquire();
    try:
      if oCdbWrapper.nApplicationResumeTime is None:
        return oCdbWrapper.nApplicationRunTime;
      return oCdbWrapper.nApplicationRunTime + time.clock() - oCdbWrapper.nApplicationResumeTime;
    finally:
      oCdbWrapper.oApplicationTimeLock.release();
  
  # Get values
  def fuGetValue(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fuGetValue(oCdbWrapper, *axArguments, **dxArguments);
  def fuGetValueForSymbol(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fuGetValueForSymbol(oCdbWrapper, *axArguments, **dxArguments);
  # Breakpoints
  def fuAddBreakpoint(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fuAddBreakpoint(oCdbWrapper, *axArguments, **dxArguments);
  def fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments);
  # Timeouts
  def fxSetTimeout(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fxSetTimeout(oCdbWrapper, *axArguments, **dxArguments);
  def fClearTimeout(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fClearTimeout(oCdbWrapper, *axArguments, **dxArguments);
  # cdb I/O
  def fasReadOutput(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fasReadOutput(oCdbWrapper, *axArguments, **dxArguments);
  def fasSendCommandAndReadOutput(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fasSendCommandAndReadOutput(oCdbWrapper, *axArguments, **dxArguments);
  
  def fasGetStack(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fasGetStack(oCdbWrapper, *axArguments, **dxArguments);
  
  def fsHTMLEncode(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fsHTMLEncode(oCdbWrapper, *axArguments, **dxArguments);
  
  def fsGetSymbolForAddress(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fsGetSymbolForAddress(oCdbWrapper, *axArguments, **dxArguments);
  
  def fsGetUnicodeString(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fsGetUnicodeString(oCdbWrapper, *axArguments, **dxArguments);
  
  def fauGetBytes(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fauGetBytes(oCdbWrapper, *axArguments, **dxArguments);
