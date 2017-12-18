import itertools, json, os, re, subprocess, sys, thread, threading, time;
from cCdbStoppedException import cCdbStoppedException;
from cCdbWrapper_fasExecuteCdbCommand import cCdbWrapper_fasExecuteCdbCommand;
from cCdbWrapper_fInterruptApplication import cCdbWrapper_fInterruptApplication;
from cCdbWrapper_fasReadOutput import cCdbWrapper_fasReadOutput;
from cCdbWrapper_fApplicationStdOutOrErrThread import cCdbWrapper_fApplicationStdOutOrErrThread;
from cCdbWrapper_fAttachToProcessesForExecutableNames import cCdbWrapper_fAttachToProcessesForExecutableNames;
from cCdbWrapper_fbAttachToProcessForId import cCdbWrapper_fbAttachToProcessForId;
from cCdbWrapper_f_Breakpoint import cCdbWrapper_fuAddBreakpoint, cCdbWrapper_fRemoveBreakpoint;
from cCdbWrapper_fCdbCleanupThread import cCdbWrapper_fCdbCleanupThread;
from cCdbWrapper_fCdbInterruptOnTimeoutThread import cCdbWrapper_fCdbInterruptOnTimeoutThread;
from cCdbWrapper_fCdbStdErrThread import cCdbWrapper_fCdbStdErrThread;
from cCdbWrapper_fCdbStdInOutThread import cCdbWrapper_fCdbStdInOutThread;
from cCdbWrapper_fsHTMLEncode import cCdbWrapper_fsHTMLEncode;
from cCdbWrapper_f_Timeout import cCdbWrapper_foSetTimeout, cCdbWrapper_fClearTimeout;
from cCollateralBugHandler import cCollateralBugHandler;
from cExcessiveCPUUsageDetector import cExcessiveCPUUsageDetector;
from cUWPApplication import cUWPApplication;
from dxConfig import dxConfig;
from mWindowsAPI import fbTerminateProcessForId, oSystemInfo;

guSymbolOptions = sum([
  0x00000001, # SYMOPT_CASE_INSENSITIVE
  0x00000002, # SYMOPT_UNDNAME
  0x00000004 * (dxConfig["bDeferredSymbolLoads"] and 1 or 0), # SYMOPT_DEFERRED_LOAD
# 0x00000008, # SYMOPT_NO_CPP
  0x00000010 * (dxConfig["bEnableSourceCodeSupport"] and 1 or 0), # SYMOPT_LOAD_LINES
# 0x00000020, # SYMOPT_OMAP_FIND_NEAREST
# 0x00000040, # SYMOPT_LOAD_ANYTHING
# 0x00000080, # SYMOPT_IGNORE_CVREC
  0x00000100 * (not dxConfig["bDeferredSymbolLoads"] and 1 or 0), # SYMOPT_NO_UNQUALIFIED_LOADS
  0x00000200, # SYMOPT_FAIL_CRITICAL_ERRORS
# 0x00000400, # SYMOPT_EXACT_SYMBOLS
  0x00000800, # SYMOPT_ALLOW_ABSOLUTE_SYMBOLS
  0x00001000 * (not dxConfig["bUse_NT_SYMBOL_PATH"] and 1 or 0), # SYMOPT_IGNORE_NT_SYMPATH
  0x00002000, # SYMOPT_INCLUDE_32BIT_MODULES 
# 0x00004000, # SYMOPT_PUBLICS_ONLY
# 0x00008000, # SYMOPT_NO_PUBLICS
  0x00010000, # SYMOPT_AUTO_PUBLICS
  0x00020000, # SYMOPT_NO_IMAGE_SEARCH
# 0x00040000, # SYMOPT_SECURE
  0x00080000, # SYMOPT_NO_PROMPTS
# 0x80000000, # SYMOPT_DEBUG (don't set here: will be switched on and off later as needed)
]);

class cCdbWrapper(object):
  def __init__(oCdbWrapper,
    sCdbISA,                                  # Which version of cdb should be used to debug this application? ("x86" or "x64")
    sApplicationBinaryPath,
    auApplicationProcessIds,
    sUWPApplicationPackageName,
    sUWPApplicationId,
    asApplicationArguments,
    asLocalSymbolPaths,
    asSymbolCachePaths, 
    asSymbolServerURLs,
    dsURLTemplate_by_srSourceFilePath,
    rImportantStdOutLines,
    rImportantStdErrLines,
    bGenerateReportHTML,        
    uProcessMaxMemoryUse,
    uTotalMaxMemoryUse,
    uMaximumNumberOfBugs,
  ):
    oCdbWrapper.aoInternalExceptions = [];
    oCdbWrapper.sCdbISA = sCdbISA or oSystemInfo.sOSISA;
    assert sApplicationBinaryPath or auApplicationProcessIds or sUWPApplicationPackageName, \
        "You must provide one of the following: an application command line, a list of process ids or an application package name";
    oCdbWrapper.sApplicationBinaryPath = sApplicationBinaryPath;
    oCdbWrapper.oUWPApplication = sUWPApplicationPackageName and cUWPApplication(sUWPApplicationPackageName, sUWPApplicationId) or None;
    oCdbWrapper.auProcessIdsPendingAttach = auApplicationProcessIds or [];
    oCdbWrapper.asApplicationArguments = asApplicationArguments;
    oCdbWrapper.asLocalSymbolPaths = asLocalSymbolPaths or [];
    oCdbWrapper.asSymbolCachePaths = asSymbolCachePaths;
    if asSymbolCachePaths is None:
      oCdbWrapper.asSymbolCachePaths = dxConfig["asDefaultSymbolCachePaths"];
    oCdbWrapper.asSymbolServerURLs = asSymbolServerURLs;
    if asSymbolServerURLs is None:
      oCdbWrapper.asSymbolServerURLs = dxConfig["asDefaultSymbolServerURLs"];
    oCdbWrapper.dsURLTemplate_by_srSourceFilePath = dsURLTemplate_by_srSourceFilePath or {};
    oCdbWrapper.rImportantStdOutLines = rImportantStdOutLines;
    oCdbWrapper.rImportantStdErrLines = rImportantStdErrLines;
    oCdbWrapper.bGenerateReportHTML = bGenerateReportHTML;
    oCdbWrapper.uProcessMaxMemoryUse = uProcessMaxMemoryUse;
    oCdbWrapper.uTotalMaxMemoryUse = uTotalMaxMemoryUse;
    oCdbWrapper.oEventCallbacksLock = threading.Lock();
    oCdbWrapper.dafEventCallbacks_by_sEventName = {
      # These are the names of all the events that cCdbWrapper can throw. If it's not in the list, you cannot use it in
      # `fAddEventCallback`, `fRemoveEventCallback`, or `fbFireEvent`.
      "Application resumed": [],
      "Application running": [],
      "Application stderr output": [],
      "Application stdout output": [],
      "Application suspended": [],
      "Attached to process": [],
      "Bug report": [],
      "Cdb stderr output": [],
      "Cdb stdin input": [],
      "Cdb stdout output": [],
      "Failed to apply application memory limits": [],
      "Failed to apply process memory limits": [],
      "Failed to debug application": [],
      "Finished": [],
      "Internal exception": [],
      "Log message": [],
      "Page heap not enabled": [],
      "Process terminated": [],
      "Started process": [],
    };

  
    # This is where we keep track of the threads that are executing (for debug purposes):
    oCdbWrapper.adxThreads = [];
    # Get the cdb binary path
    oCdbWrapper.sDebuggingToolsPath = dxConfig["sDebuggingToolsPath_%s" % oCdbWrapper.sCdbISA];
    assert oCdbWrapper.sDebuggingToolsPath, "No %s Debugging Tools for Windows path found" % oCdbWrapper.sCdbISA;
    oCdbWrapper.doProcess_by_uId = {};
    oCdbWrapper.doConsoleProcess_by_uId = {};
    oCdbWrapper.oCurrentProcess = None; # The current process id in cdb's context
    # Keep track of what the applications "main" processes are.
    oCdbWrapper.aoMainProcesses = [];
    # Initialize some variables
    oCdbWrapper.sCurrentISA = None; # During exception handling, this is set to the ISA for the code that caused it.
    if bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML = ""; # Logs stdin/stdout/stderr for the cdb process, grouped by executed command.
      oCdbWrapper.sPromptHTML = None; # Logs cdb prompt to be adde to CdbIOHTML if a command is added.
      if dxConfig["bLogInReport"]:
        oCdbWrapper.sLogHTML = ""; # Logs various events that may be relevant
    oCdbWrapper.bCdbRunning = True; # Set to False after cdb terminated, used to terminate the debugger thread.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = False; # Set to True when cdb is terminated on purpose, used to detect unexpected termination.
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
    # Keep track of timeouts that should fire at some point in the future and timeouts that should fire now.
    oCdbWrapper.aoTimeouts = [];
    oCdbWrapper.bApplicationIsRunnning = False; # Will be set to true while the application is running in cdb.
    oCdbWrapper.uUtilityInterruptThreadId = None; # Will be set to the thread id in which we triggered an AV to
                                                  # interrupt the application.
    # Lock for the above four timeout and interrupt variables
    oCdbWrapper.oTimeoutAndInterruptLock = threading.RLock();
    # Keep track of how long the application has been running, used for timeouts (see foSetTimeout, fCdbStdInOutThread
    # and fCdbInterruptOnTimeoutThread for details. The debugger can tell is what time it thinks it is before we start
    # and resume the application as well as what time it thinks it was when an exception happened. The difference is
    # used to calculate how long the application has been running. We cannot simply use time.clock() before start/
    # resuming and at the time an event is handled as the debugger may take quite some time processing an event before
    # we can call time.clock(): this time would incorrectly be added to the time the application has spent running.
    # However, while the application is running, we cannot ask the debugger what time it thinks it is, so we have to 
    # rely on time.clock(). Hence, both values are tracked.
    oCdbWrapper.oApplicationTimeLock = threading.RLock();
    oCdbWrapper.nConfirmedApplicationRunTime = 0; # Total time spent running before last interruption
    oCdbWrapper.nApplicationResumeDebuggerTime = None;  # debugger time at the moment the application was last resumed
    oCdbWrapper.nApplicationResumeTime = None;          # time.clock() at the moment the application was last resumed
    oCdbWrapper.oCdbProcess = None;
    # We track stderr output, as it may contain information output by AddressSanitizer when it detects an issue. Once
    # ASan is done outputting everthing it knows and causes an exception to terminate the application, we can analyze
    # its output and use it to create a bug id & report.
    oCdbWrapper.asStdErrOutput = [];
    
    oCdbWrapper.oCollateralBugHandler = cCollateralBugHandler(oCdbWrapper, uMaximumNumberOfBugs);
    oCdbWrapper.bFatalBugDetected = False;
  
  def fAttachToProcessById(oCdbWrapper, uProcessId):
    if oCdbWrapper.oCdbProcess is None:
      # This is the first process: start the debugger and attach to it.
      assert len(oCdbWrapper.auProcessIdsPendingAttach) == 0, \
          "This functions is not expected to get called when processes are pending attach.";
      oCdbWrapper.auProcessIdsPendingAttach.append(uProcessId);
      oCdbWrapper.__fStartDebugger();
    else:
      oCdbWrapper.fInterrupt(
        "Attaching to process",
        oCdbWrapper.__fActuallyAttachToProcessById,
        uProcessId
      );
  
  def __fActuallyAttachToProcessById(oCdbWrapper, uProcessId):
    asAttachToProcess = oCdbWrapper.fasExecuteCdbCommand( \
      sCommand = ".attach 0x%X;" % uProcessId,
      sComment = "Attach to process %d" % uProcessId
    );
    assert asAttachToProcess == ["Attach will occur on next execution"], \
        "Unexpected .attach output: %s" % repr(asAttachToProcess);
  
  def fStart(oCdbWrapper):
    global guSymbolOptions;
    oCdbWrapper.bDebuggerStarted = True;
    # Get the command line (without starting/attaching to a process)
    fQuote = lambda sArgument: '"%s"' % sArgument.replace('"', '\\"');
    asCommandLine = [
      fQuote(os.path.join(oCdbWrapper.sDebuggingToolsPath, "cdb.exe")),
      "-o", # Debug any child processes spawned by the main processes as well.
      "-sflags", "0x%08X" % guSymbolOptions # Set symbol loading options (See above for details)
    ];
    if dxConfig["bEnableSourceCodeSupport"]:
      asCommandLine += ["-lines"];
    # Construct the cdb symbol path if one is needed and add it as an argument.
    sSymbolsPath = ";".join(
      oCdbWrapper.asLocalSymbolPaths +
      ["cache*%s" % x for x in oCdbWrapper.asSymbolCachePaths] +
      ["srv*%s" % x for x in oCdbWrapper.asSymbolServerURLs]
    );
    if sSymbolsPath:
      asCommandLine += ["-y", fQuote(sSymbolsPath)];
    # Create a thread that interacts with the debugger to debug the application
    oCdbWrapper.oCdbStdInOutThread = oCdbWrapper.foHelperThread(oCdbWrapper.fCdbStdInOutThread, bVital = True);
    # Create a thread that reads stderr output and shows it in the console
    oCdbWrapper.oCdbStdErrThread = oCdbWrapper.foHelperThread(oCdbWrapper.fCdbStdErrThread, bVital = True);
    # Create a thread that waits for the debugger to terminate and cleans up after it.
    oCdbWrapper.oCdbCleanupThread = oCdbWrapper.foHelperThread(oCdbWrapper.fCdbCleanupThread, bVital = True);
    # We first start a utility process that we can use to trigger breakpoints in, so we can distinguish them from
    # breakpoints triggered in the target application.
    asCommandLine += [
      fQuote(os.getenv("ComSpec")), "/K", fQuote("ECHO OFF"), 
    ];
    oCdbWrapper.uUtilityProcessId = None;
    if oCdbWrapper.sApplicationBinaryPath is not None:
      # If a process must be started, add it to the command line.
      assert not oCdbWrapper.auProcessIdsPendingAttach, \
          "Cannot start a process and attach to processes at the same time";
    elif oCdbWrapper.oUWPApplication:
      assert len(oCdbWrapper.asApplicationArguments) <= 1, \
          "You cannot specify multiple arguments for a UWP application.";
    else:
      assert oCdbWrapper.auProcessIdsPendingAttach, \
          "Must start a process or attach to one";
    # Show the command line if requested.
    oCdbWrapper.sCdbCommandLine = " ".join(asCommandLine);
    oCdbWrapper.oCdbProcess = subprocess.Popen(
      args = oCdbWrapper.sCdbCommandLine,
      stdin = subprocess.PIPE,
      stdout = subprocess.PIPE,
      stderr = subprocess.PIPE,
      creationflags = subprocess.CREATE_NEW_PROCESS_GROUP,
    );
    oCdbWrapper.oCdbStdInOutThread.start();
    oCdbWrapper.oCdbStdErrThread.start();
    oCdbWrapper.oCdbCleanupThread.start();
  
  def foHelperThread(oCdbWrapper, fActivity, *axActivityArguments, **dxFlags):
    for sFlag in dxFlags:
      assert sFlag in ["bVital"], \
          "Unknown flag %s" % sFlag;
    bVital = dxFlags.get("bVital", False);
    try:
      return threading.Thread(target = oCdbWrapper.__fThreadWrapper, args = (bVital, fActivity, axActivityArguments));
    except thread.error as oException:
      # We cannot create another thread. The most obvious reason for this error is that there are too many threads
      # already. This might be cause by our threads not terminating as expected. To debug this, we will dump the
      # running threads, so we might detect any threads that should have terminated but haven't.
      print "Threads:";
      for dxThread in oCdbWrapper.adxThreads:
        print "%04d %s(%s)" % (dxThread["oThread"].ident, repr(dxThread["fActivity"]), ", ".join([repr(xArgument) for xArgument in dxThread["axActivityArguments"]]));
      raise;
  
  def __fThreadWrapper(oCdbWrapper, bVital, fActivity, axActivityArguments):
    dxThread = {"fActivity": fActivity, "oThread": threading.currentThread(), "axActivityArguments": axActivityArguments}; 
    oCdbWrapper.adxThreads.append(dxThread);
    try:
      try:
        fActivity(*axActivityArguments);
      except cCdbStoppedException as oCdbStoppedException:
        # There is only one type of exception that is expected which is raised in the cdb stdin/out thread when cdb has
        # terminated. This exception is only used to terminate that thread and should be caught and handled here, to
        # prevent it from being reported as an (unexpected) internal exception.
        pass;
      except Exception, oException:
        oCdbWrapper.aoInternalExceptions.append(oException);
        cException, oException, oTraceBack = sys.exc_info();
        if not oCdbWrapper.fbFireEvent("Internal exception", oException, oTraceBack):
          raise;
    finally:
      try:
        if bVital and oCdbWrapper.bCdbRunning:
          oCdbProcess = getattr(oCdbWrapper, "oCdbProcess", None);
          if not oCdbProcess:
            oCdbWrapper.bCdbRunning = False;
            return;
          if oCdbProcess.poll() is not None:
            oCdbWrapper.bCdbRunning = False;
            return;
          # A vital thread terminated and cdb is still running: terminate cdb
          assert fbTerminateProcessForId(oCdbProcess.pid), \
              "Could not terminate cdb";
          oCdbWrapper.bCdbRunning = False;
      finally:
        oCdbWrapper.adxThreads.remove(dxThread);
  
  def fTerminate(oCdbWrapper):
    # Call `fTerminate` when you need to stop cBugId asap, e.g. when an internal error is detected. This function does
    # not wait for it to stop.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
    oCdbProcess = getattr(oCdbWrapper, "oCdbProcess", None);
    if oCdbProcess:
      try:
        oCdbProcess.terminate();
      except:
        pass;
  
  def fStop(oCdbWrapper):
    # Call `fStop` to cleanly terminate cdb, and therefore cBugId, and wait for it to finish.
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
    assert not oCdbProcess or oCdbProcess.poll() is not None, \
        "cCdbWrapper is being destroyed while cdb is still running.";
  
  @property
  def bUsingSymbolServers(oCdbWrapper):
    return len(oCdbWrapper.asSymbolServerURLs) > 0;
  
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
    if uProcessId is not None and (oCdbWrapper.oCurrentProcess is None or uProcessId != oCdbWrapper.oCurrentProcess.uId):
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
      asSelectCommandOutput = oCdbWrapper.fasExecuteCdbCommand(
        sCommand = sSelectCommand,
        sComment = "Select %s" % "/".join(asSelected),
      );
      # cdb may or may not output the last instruction :S. But it will always output the isa on the last line if selected.
      if "isa" in asSelected:
        bUnexpectedOutput = asSelectCommandOutput[-1] not in [
          "Effective machine: x86 compatible (x86)",
          "Effective machine: x64 (AMD64)"
        ];
      else:
        bUnexpectedOutput = False; #len(asSelectCommandOutput) != 0;
      assert not bUnexpectedOutput, \
          "Unexpected select %s output:\r\n%s" % ("/".join(asSelected), "\r\n".join(asSelectCommandOutput));
  
  # Excessive CPU usage
  def fSetCheckForExcessiveCPUUsageTimeout(oCdbWrapper, nTimeout):
    oCdbWrapper.oExcessiveCPUUsageDetector.fStartTimeout(nTimeout);
  
  @property
  def nApplicationRunTime(oCdbWrapper):
    # This can be exact (when the application is suspended) or an estimate (when the application is running).
    if not oCdbWrapper.bApplicationIsRunnning:
      # Fast and exact path.
      return oCdbWrapper.nConfirmedApplicationRunTime;
    oCdbWrapper.oApplicationTimeLock.acquire();
    try:
      return oCdbWrapper.nConfirmedApplicationRunTime + time.clock() - oCdbWrapper.nApplicationResumeTime;
    finally:
      oCdbWrapper.oApplicationTimeLock.release();
  
  # Breakpoints
  def fuAddBreakpoint(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fuAddBreakpoint(oCdbWrapper, *axArguments, **dxArguments);
  def fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments);
  # Timeouts/interrupt
  def foSetTimeout(oCdbWrapper, sDescription, nTimeToWait, fCallback, *axCallbackArguments):
    return cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, nTimeToWait, fCallback, *axCallbackArguments);
  def fInterrupt(oCdbWrapper, sDescription, fCallback, *axCallbackArguments):
    # An interrupt is implemented as an immediate timeout
    cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, 0, fCallback, *axCallbackArguments);
  def fClearTimeout(oCdbWrapper, oTimeout):
    return cCdbWrapper_fClearTimeout(oCdbWrapper, oTimeout);
  # cdb I/O
  def fasReadOutput(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fasReadOutput(oCdbWrapper, *axArguments, **dxArguments);
  def fasExecuteCdbCommand(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fasExecuteCdbCommand(oCdbWrapper, *axArguments, **dxArguments);
  
  def fsHTMLEncode(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fsHTMLEncode(oCdbWrapper, *axArguments, **dxArguments);
  
  def fAttachToProcessesForExecutableNames(oCdbWrapper, *asBinaryNames):
    return cCdbWrapper_fAttachToProcessesForExecutableNames(oCdbWrapper, *asBinaryNames);
  
  def fbAttachToProcessForId(oCdbWrapper, uProcessId):
    return cCdbWrapper_fbAttachToProcessForId(oCdbWrapper, uProcessId);
  
  def fInterruptApplication(oCdbWrapper):
    cCdbWrapper_fInterruptApplication(oCdbWrapper);
  
  def fLogMessageInReport(oCdbWrapper, sMessageClass, sMessage):
    oCdbWrapper.fbFireEvent("Log message", sMessageClass, sMessage);
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      oCdbWrapper.sLogHTML += "<span class=\"%s\">%s</span><br/>" % \
          (oCdbWrapper.fsHTMLEncode(sMessageClass), oCdbWrapper.fsHTMLEncode(sMessage));
  
  def fCdbStdInOutThread(oCdbWrapper):
    return cCdbWrapper_fCdbStdInOutThread(oCdbWrapper);
  
  def fCdbStdErrThread(oCdbWrapper):
    return cCdbWrapper_fCdbStdErrThread(oCdbWrapper);
  
  def fCdbCleanupThread(oCdbWrapper):
    return cCdbWrapper_fCdbCleanupThread(oCdbWrapper);
  
  def fCdbInterruptOnTimeoutThread(oCdbWrapper):
    return cCdbWrapper_fCdbInterruptOnTimeoutThread(oCdbWrapper);
  
  def fApplicationStdOutOrErrThread(oCdbWraper, uProcessId, sBinaryName, sCommandLine, oStdOutOrErrPipe, sStdOutOrErr):
    return cCdbWrapper_fApplicationStdOutOrErrThread(oCdbWraper, uProcessId, sBinaryName, sCommandLine, oStdOutOrErrPipe, sStdOutOrErr);
  
  def fAddEventCallback(oCdbWrapper, sEventName, fCallback):
    assert sEventName in oCdbWrapper.dafEventCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    oCdbWrapper.oEventCallbacksLock.acquire();
    try:
      oCdbWrapper.dafEventCallbacks_by_sEventName[sEventName].append(fCallback);
    finally:
      oCdbWrapper.oEventCallbacksLock.release();
  
  def fRemoveEventCallback(oCdbWrapper, sEventName, fCallback):
    assert sEventName in oCdbWrapper.dafEventCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    oCdbWrapper.oEventCallbacksLock.acquire();
    try:
      oCdbWrapper.dafEventCallbacks_by_sEventName[sEventName].remove(fCallback);
    finally:
      oCdbWrapper.oEventCallbacksLock.release();
  
  def fbFireEvent(oCdbWrapper, sEventName, *axCallbackArguments):
    assert sEventName in oCdbWrapper.dafEventCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    oCdbWrapper.oEventCallbacksLock.acquire();
    try:
      afCallbacks = oCdbWrapper.dafEventCallbacks_by_sEventName[sEventName][:];
    finally:
      oCdbWrapper.oEventCallbacksLock.release();
    for fCallback in afCallbacks:
      fCallback(*axCallbackArguments);
    return len(afCallbacks) != 0;
