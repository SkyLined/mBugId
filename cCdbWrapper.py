import itertools, json, os, re, subprocess, sys, thread, threading, time;
from cCdbStoppedException import cCdbStoppedException;
from cCdbWrapper_fasExecuteCdbCommand import cCdbWrapper_fasExecuteCdbCommand;
from cCdbWrapper_fInterruptApplicationExecution import cCdbWrapper_fInterruptApplicationExecution;
from cCdbWrapper_fasReadOutput import cCdbWrapper_fasReadOutput;
from cCdbWrapper_fApplicationStdOutOrErrThread import cCdbWrapper_fApplicationStdOutOrErrThread;
from cCdbWrapper_fAttachToProcessesForExecutableNames import cCdbWrapper_fAttachToProcessesForExecutableNames;
from cCdbWrapper_fAttachToProcessForId import cCdbWrapper_fAttachToProcessForId;
from cCdbWrapper_foStartApplicationProcess import cCdbWrapper_foStartApplicationProcess;
from cCdbWrapper_fCdbCleanupThread import cCdbWrapper_fCdbCleanupThread;
from cCdbWrapper_fCdbInterruptOnTimeoutThread import cCdbWrapper_fCdbInterruptOnTimeoutThread;
from cCdbWrapper_fCdbStdErrThread import cCdbWrapper_fCdbStdErrThread;
from cCdbWrapper_fCdbStdInOutThread import cCdbWrapper_fCdbStdInOutThread;
from cCdbWrapper_fHandleNewApplicationProcess import cCdbWrapper_fHandleNewApplicationProcess;
from cCdbWrapper_fHandleNewUtilityProcess import cCdbWrapper_fHandleNewUtilityProcess;
from cCdbWrapper_fHandleApplicationProcessTermination import cCdbWrapper_fHandleApplicationProcessTermination;
from cCdbWrapper_fRemoveBreakpoint import cCdbWrapper_fRemoveBreakpoint;
from cCdbWrapper_fRunTimeoutCallbacks import cCdbWrapper_fRunTimeoutCallbacks;
from cCdbWrapper_fSelectProcessAndThread import cCdbWrapper_fSelectProcessAndThread;
from cCdbWrapper_fStartUWPApplication import cCdbWrapper_fStartUWPApplication;
from cCdbWrapper_fTerminateUWPApplication import cCdbWrapper_fTerminateUWPApplication;
from cCdbWrapper_fsHTMLEncode import cCdbWrapper_fsHTMLEncode;
from cCdbWrapper_f_Timeout import cCdbWrapper_foSetTimeout, cCdbWrapper_fClearTimeout;
from cCdbWrapper_fuAddBreakpointForAddress import cCdbWrapper_fuAddBreakpointForAddress;
from cCdbWrapper_fuAddBreakpointForSymbol import cCdbWrapper_fuAddBreakpointForSymbol;
from cCollateralBugHandler import cCollateralBugHandler;
from cExcessiveCPUUsageDetector import cExcessiveCPUUsageDetector;
from cUWPApplication import cUWPApplication;
from cVerifierStopDetector import cVerifierStopDetector;
from dxConfig import dxConfig;
from mWindowsAPI import cConsoleProcess, fbTerminateProcessForId, oSystemInfo;

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
    bGenerateReportHTML,        
    uProcessMaxMemoryUse,
    uTotalMaxMemoryUse,
    uMaximumNumberOfBugs,
  ):
    oCdbWrapper.sCdbISA = sCdbISA or oSystemInfo.sOSISA;
    assert sApplicationBinaryPath or auApplicationProcessIds or sUWPApplicationPackageName, \
        "You must provide one of the following: an application command line, a list of process ids or an application package name";
    oCdbWrapper.sApplicationBinaryPath = sApplicationBinaryPath;
    oCdbWrapper.oUWPApplication = sUWPApplicationPackageName and cUWPApplication(sUWPApplicationPackageName, sUWPApplicationId) or None;
    oCdbWrapper.auApplicationProcessIds = auApplicationProcessIds or [];
    oCdbWrapper.auMainProcessIds = oCdbWrapper.auApplicationProcessIds[:];
    oCdbWrapper.bApplicationStarted = False;
    oCdbWrapper.bUWPApplicationStarted = False;
    oCdbWrapper.bStopping = False;
    oCdbWrapper.auProcessIdsPendingAttach = [];
    oCdbWrapper.auProcessIdsThatNeedToBeResumedAfterAttaching = [];
    oCdbWrapper.asApplicationArguments = asApplicationArguments;
    oCdbWrapper.asLocalSymbolPaths = asLocalSymbolPaths or [];
    oCdbWrapper.asSymbolCachePaths = asSymbolCachePaths;
    if asSymbolCachePaths is None:
      oCdbWrapper.asSymbolCachePaths = dxConfig["asDefaultSymbolCachePaths"];
    oCdbWrapper.asSymbolServerURLs = asSymbolServerURLs;
    if asSymbolServerURLs is None:
      oCdbWrapper.asSymbolServerURLs = dxConfig["asDefaultSymbolServerURLs"];
    oCdbWrapper.dsURLTemplate_by_srSourceFilePath = dsURLTemplate_by_srSourceFilePath or {};
    oCdbWrapper.bGenerateReportHTML = bGenerateReportHTML;
    oCdbWrapper.uProcessMaxMemoryUse = uProcessMaxMemoryUse;
    oCdbWrapper.uTotalMaxMemoryUse = uTotalMaxMemoryUse;
    oCdbWrapper.oEventCallbacksLock = threading.Lock();
    oCdbWrapper.dafEventCallbacks_by_sEventName = {
      # These are the names of all the events that cCdbWrapper can throw. If it's not in the list, you cannot use it in
      # `fAddEventCallback`, `fRemoveEventCallback`, or `fbFireEvent`. The same event names are used by cBugId, but
      # any
      "Application resumed": [], # ()
      "Application running": [], # ()
      "Application debug output": [], # (str[] asOutput)
      "Application stderr output": [], # (str sOutput)
      "Application stdout output": [], # (str sOutput)
      "Application suspended": [], # (str sReason)
      "Attached to process": [], # (mWindowsAPI.cProcess oProcess)
      "Bug report": [], # (cBugReport oBugReport)
      "Cdb stderr output": [], # (str sOutput)
      "Cdb stdin input": [], # (str sInput)
      "Cdb stdout output": [], # (str sOutput)
      "Failed to apply application memory limits": [], # (mWindowsAPI.cProcess oProcess)
      "Failed to apply process memory limits": [], # (mWindowsAPI.cProcess oProcess)
      "Failed to debug application": [], # (str sReason)
      "Finished": [], # ()
      "Internal exception": [], # (Exception oException, traceback oTraceBack)
      "Log message": [], # (str sDescription, dict dxData)
      "Page heap not enabled": [], # (mWindowsAPI.cProcess oProcess, bool bPreventable)
      "Process started": [], # (mWindowsAPI.cConsoleProcess oConsoleProcess)
      "Process terminated": [], #(mWindowsAPI.cProcess oProcess)
    };

  
    # This is where we keep track of the threads that are executing (for debug purposes):
    oCdbWrapper.adxThreads = [];
    # Get the cdb binary path
    oCdbWrapper.sDebuggingToolsPath = dxConfig["sDebuggingToolsPath_%s" % oCdbWrapper.sCdbISA];
    assert oCdbWrapper.sDebuggingToolsPath, "No %s Debugging Tools for Windows path found" % oCdbWrapper.sCdbISA;
    oCdbWrapper.doProcess_by_uId = {};
    oCdbWrapper.doConsoleProcess_by_uId = {};
    oCdbWrapper.oCurrentProcess = None; # The current process id in cdb's context
    # Initialize some variables
    oCdbWrapper.sCurrentISA = None; # During exception handling, this is set to the ISA for the code that caused it.
    if bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML = ""; # Logs stdin/stdout/stderr for the cdb process, grouped by executed command.
      oCdbWrapper.sPromptHTML = None; # Logs cdb prompt to be adde to CdbIOHTML if a command is added.
      if dxConfig["bLogInReport"]:
        oCdbWrapper.sLogHTML = ""; # Logs various events that may be relevant
    oCdbWrapper.bCdbRunning = True; # Set to False after cdb terminated, used to terminate the debugger thread.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = False; # Set to True when cdb is terminated on purpose, used to detect unexpected termination.
    # To make it easier to refer to cdb breakpoints by id, a mechanism must be used to allocate and release them
    # See fuGetBreakpointId and fReleaseBreakpointId for implementation details.
    oCdbWrapper.oBreakpointCounter = itertools.count(); # None have been used so far, so start at 0.
    # You can set a breakpoint that results in a bug being reported when it is hit.
    # See fuAddBugBreakpoint and fReleaseBreakpointId for implementation details.
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
    oCdbWrapper.oCdbConsoleProcess = None;
    # We track stderr output, as it may contain information output by AddressSanitizer when it detects an issue. Once
    # ASan is done outputting everthing it knows and causes an exception to terminate the application, we can analyze
    # its output and use it to create a bug id & report.
    oCdbWrapper.asStdErrOutput = [];
    
    oCdbWrapper.oCollateralBugHandler = cCollateralBugHandler(oCdbWrapper, uMaximumNumberOfBugs);
    
    # Create a verifier stop detector
    cVerifierStopDetector(oCdbWrapper);
    
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      def fWriteLogMessageToReport(sMessage, dsData = None):
        sData = dsData and ", ".join(["%s: %s" % (sName, sValue) for (sName, sValue) in dsData.items()]);
        oCdbWrapper.sLogHTML += "<span class=\"%s\">%s%s</span><br/>" % \
            (oCdbWrapper.fsHTMLEncode(sMessage), sData and " (%s)" % oCdbWrapper.fsHTMLEncode(sData) or "");
      oCdbWrapper.fAddEventCallback("Log message", fWriteLogMessageToReport);
  
  @property
  def bUsingSymbolServers(oCdbWrapper):
    return len(oCdbWrapper.asSymbolServerURLs) > 0;
  
  def foHelperThread(oCdbWrapper, fActivity, *axActivityArguments, **dxFlags):
    for sFlag in dxFlags:
      assert sFlag in ["bVital"], \
          "Unknown flag %s" % sFlag;
    bVital = dxFlags.get("bVital", False);
    def fThreadWrapper():
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
          cException, oException, oTraceBack = sys.exc_info();
          if not oCdbWrapper.fbFireEvent("Internal exception", oException, oTraceBack):
            oCdbWrapper.fTerminate();
            raise;
      finally:
        try:
          if bVital and oCdbWrapper.bCdbRunning:
            if oCdbWrapper.oCdbConsoleProcess and oCdbWrapper.oCdbConsoleProcess.bIsRunning:
              # A vital thread terminated and cdb is still running: terminate cdb
              oCdbWrapper.oCdbConsoleProcess.fbTerminate()
              assert not oCdbWrapper.oCdbConsoleProcess.bIsRunning, \
                  "Could not terminate cdb";
            oCdbWrapper.bCdbRunning = False;
        finally:
          oCdbWrapper.adxThreads.remove(dxThread);
    try:
      return threading.Thread(target = fThreadWrapper);
    except thread.error as oException:
      # We cannot create another thread. The most obvious reason for this error is that there are too many threads
      # already. This might be cause by our threads not terminating as expected. To debug this, we will dump the
      # running threads, so we might detect any threads that should have terminated but haven't.
      print "Threads:";
      for dxThread in oCdbWrapper.adxThreads:
        print "%04d %s(%s)" % (dxThread["oThread"].ident, repr(dxThread["fActivity"]), ", ".join([repr(xArgument) for xArgument in dxThread["axActivityArguments"]]));
      raise;
  
  def fStart(oCdbWrapper):
    global guSymbolOptions;
    # Create a thread that interacts with the debugger to debug the application
    oCdbWrapper.oCdbStdInOutThread = oCdbWrapper.foHelperThread(oCdbWrapper.fCdbStdInOutThread, bVital = True);
    # Create a thread that reads stderr output and shows it in the console
    oCdbWrapper.oCdbStdErrThread = oCdbWrapper.foHelperThread(oCdbWrapper.fCdbStdErrThread, bVital = True);
    # Create a thread that waits for the debugger to terminate and cleans up after it.
    oCdbWrapper.oCdbCleanupThread = oCdbWrapper.foHelperThread(oCdbWrapper.fCdbCleanupThread, bVital = True);
    # We first start a utility process that we can use to trigger breakpoints in, so we can distinguish them from
    # breakpoints triggered in the target application.
    oCdbWrapper.uUtilityProcessId = None;
    if oCdbWrapper.sApplicationBinaryPath is not None:
      # If a process must be started, add it to the command line.
      assert not oCdbWrapper.auApplicationProcessIds, \
          "Cannot start a process and attach to processes at the same time";
    elif oCdbWrapper.oUWPApplication:
      assert len(oCdbWrapper.asApplicationArguments) <= 1, \
          "You cannot specify multiple arguments for a UWP application.";
    else:
      assert oCdbWrapper.auApplicationProcessIds, \
          "Must start a process or attach to one";
    # Get the command line arguments for cdbe.exe
    # Construct the cdb symbol path if one is needed and add it as an argument.
    sSymbolsPath = ";".join(
      oCdbWrapper.asLocalSymbolPaths +
      ["cache*%s" % x for x in oCdbWrapper.asSymbolCachePaths] +
      ["srv*%s" % x for x in oCdbWrapper.asSymbolServerURLs]
    );
    asArguments = [
      # Debug any child processes spawned by the main processes as well.
      "-o", 
      # Set symbol loading options (See above for details)
      "-sflags", "0x%08X" % guSymbolOptions, 
#      "-sxe", "ld:verifier", # Breakpoint when verifier is loaded, so we can set a breakpoint on VERIFIER STOPs.
    ] + (dxConfig["bEnableSourceCodeSupport"] and [
      "-lines",
    ] or []) + (sSymbolsPath and [
      "-y", sSymbolsPath,
    ] or []) + [
      os.getenv("ComSpec"), "/K", "ECHO OFF", 
    ];
    oCdbWrapper.oCdbConsoleProcess = cConsoleProcess.foCreateForBinaryPathAndArguments(
      sBinaryPath = os.path.join(oCdbWrapper.sDebuggingToolsPath, "cdb.exe"),
      asArguments = asArguments,
    );
    oCdbWrapper.oCdbStdInOutThread.start();
    oCdbWrapper.oCdbStdErrThread.start();
    oCdbWrapper.oCdbCleanupThread.start();
    # If we need to start a binary for this application, do so:
    if oCdbWrapper.sApplicationBinaryPath:
      oMainConsoleProcess = oCdbWrapper.foStartApplicationProcess(
        oCdbWrapper.sApplicationBinaryPath,
        oCdbWrapper.asApplicationArguments
      );
      if oMainConsoleProcess is None:
        oCdbWrapper.fStop();
        return;
      oCdbWrapper.auMainProcessIds.append(oMainConsoleProcess.uId);
    # If we need to attach to existing application processes, do so:
    for uProcessId in oCdbWrapper.auApplicationProcessIds:
      # We assume all application processes have been suspended. This makes sense because otherwise they might crash
      # before BugId has a chance to attach.
      oCdbWrapper.fAttachToProcessForId(uProcessId, bMustBeResumed = True);
  
  def fTerminate(oCdbWrapper):
    # Call `fTerminate` when you need to stop cBugId asap, e.g. when an internal error is detected. This function does
    # not wait for it to stop.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
    if oCdbWrapper.oCdbConsoleProcess:
      assert oCdbWrapper.oCdbConsoleProcess.fbTerminate(5), \
          "Failed to terminate cdb.exe process within 5 seconds";
  
  def fStop(oCdbWrapper):
    # Call `fStop` to cleanly terminate cdb, and therefore cBugId, and wait for it to finish.
    oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
    # Tell the cdb stdin/out thread we are stopping, so it executes a "q" command and terminates as soon as possible.
    oCdbWrapper.bStopping = True; 
    # Interrupt the application if it is running, to make sure the stdin/out thread has a chance to execute a command.
    if oCdbWrapper.bApplicationIsRunnning:
      oCdbWrapper.fInterruptApplicationExecution();
  
  def __del__(oCdbWrapper):
    # Check to make sure the debugger process is not running
    try:
      oCdbConsoleProcess = oCdbWrapper.oCdbConsoleProcess;
    except:
      # The object may already have been deleted.
      pass;
    else:
      assert not oCdbConsoleProcess or not oCdbConsoleProcess.bRunning, \
          "cCdbWrapper is being destroyed while cdb.exe is still running.";
  
  # Select process/thread
  def fSelectProcess(oCdbWrapper, uProcessId):
    return oCdbWrapper.fSelectProcessAndThread(uProcessId = uProcessId);
  def fSelectThread(oCdbWrapper, uThreadId):
    return oCdbWrapper.fSelectProcessAndThread(uThreadId = uThreadId);
  def fSelectProcessAndThread(oCdbWrapper, uProcessId = None, uThreadId = None):
    return cCdbWrapper_fSelectProcessAndThread(oCdbWrapper, uProcessId, uThreadId);
  
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
  def fuAddBreakpointForAddress(oCdbWrapper, uAddress, fCallback, uProcessId, uThreadId = None, sCommand = None):
    return cCdbWrapper_fuAddBreakpointForAddress(oCdbWrapper, uAddress, fCallback, uProcessId, uThreadId, sCommand);
  def fuAddBreakpointForSymbol(ooCdbWrapper, sSymbol, fCallback, uProcessId, uThreadId = None, sCommand = None):
    return cCdbWrapper_fuAddBreakpointForSymbol(ooCdbWrapper, sSymbol, fCallback, uProcessId, uThreadId, sCommand);
  def fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments);
  
  # Timeouts/interrupt
  def foSetTimeout(oCdbWrapper, sDescription, nTimeToWait, fCallback, *axCallbackArguments):
    return cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, nTimeToWait, fCallback, *axCallbackArguments);
  def fInterrupt(oCdbWrapper, sDescription, fCallback, *axCallbackArguments):
    # An interrupt == an immediate timeout
    cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, 0, fCallback, *axCallbackArguments);
  def fClearTimeout(oCdbWrapper, oTimeout):
    return cCdbWrapper_fClearTimeout(oCdbWrapper, oTimeout);
  def fCdbInterruptOnTimeoutThread(oCdbWrapper):
    return cCdbWrapper_fCdbInterruptOnTimeoutThread(oCdbWrapper);
  def fRunTimeoutCallbacks(oCdbWrapper):
    cCdbWrapper_fRunTimeoutCallbacks(oCdbWrapper);
  
  # cdb I/O
  def fasReadOutput(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fasReadOutput(oCdbWrapper, *axArguments, **dxArguments);
  def fasExecuteCdbCommand(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fasExecuteCdbCommand(oCdbWrapper, *axArguments, **dxArguments);
  
  def fsHTMLEncode(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fsHTMLEncode(oCdbWrapper, *axArguments, **dxArguments);
  
  def fInterruptApplicationExecution(oCdbWrapper):
    cCdbWrapper_fInterruptApplicationExecution(oCdbWrapper);
  
  # stdin/out/err handling threads
  def fCdbStdInOutThread(oCdbWrapper):
    return cCdbWrapper_fCdbStdInOutThread(oCdbWrapper);
  def fCdbStdErrThread(oCdbWrapper):
    return cCdbWrapper_fCdbStdErrThread(oCdbWrapper);
  def fCdbCleanupThread(oCdbWrapper):
    return cCdbWrapper_fCdbCleanupThread(oCdbWrapper);
  def fApplicationStdOutOrErrThread(oCdbWraper, oConsoleProcess, oStdOutOrErrPipe):
    return cCdbWrapper_fApplicationStdOutOrErrThread(oCdbWraper, oConsoleProcess, oStdOutOrErrPipe);
  
  # Event handling
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
  
  # Start/attach to processes
  def foStartApplicationProcess(oCdbWrapper, sBinaryPath, asArguments):
    return cCdbWrapper_foStartApplicationProcess(oCdbWrapper, sBinaryPath, asArguments);
  def fAttachToProcessForId(oCdbWrapper, uProcessId, bMustBeResumed = False):
    return cCdbWrapper_fAttachToProcessForId(oCdbWrapper, uProcessId, bMustBeResumed);
  def fAttachToProcessesForExecutableNames(oCdbWrapper, *asBinaryNames):
    return cCdbWrapper_fAttachToProcessesForExecutableNames(oCdbWrapper, *asBinaryNames);
  # Start/stop UWP applications.
  def fStartUWPApplication(oCdbWrapper, oUWPApplication, sArgument):
    return cCdbWrapper_fStartUWPApplication(oCdbWrapper, oUWPApplication, sArgument);
  def fTerminateUWPApplication(oCdbWrapper, oUWPApplication):
    return cCdbWrapper_fTerminateUWPApplication(oCdbWrapper, oUWPApplication);
  
  # Handle process start & termination
  def fHandleNewApplicationProcess(oCdbWrapper, uProcessId):
    return cCdbWrapper_fHandleNewApplicationProcess(oCdbWrapper, uProcessId);
  def fHandleNewUtilityProcess(oCdbWrapper, uProcessId):
    return cCdbWrapper_fHandleNewUtilityProcess(oCdbWrapper, uProcessId);
  def fHandleApplicationProcessTermination(oCdbWrapper, uProcessId):
    return cCdbWrapper_fHandleApplicationProcessTermination(oCdbWrapper, uProcessId);
    
