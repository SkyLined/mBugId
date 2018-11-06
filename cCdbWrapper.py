import itertools, json, os, re, subprocess, sys, thread, threading, time;
from .cASanErrorDetector import cASanErrorDetector;
from .cCdbStoppedException import cCdbStoppedException;
from .cCdbWrapper_fApplicationStdOutOrErrHelperThread import cCdbWrapper_fApplicationStdOutOrErrHelperThread;
from .cCdbWrapper_fasExecuteCdbCommand import cCdbWrapper_fasExecuteCdbCommand;
from .cCdbWrapper_fasReadOutput import cCdbWrapper_fasReadOutput;
from .cCdbWrapper_fAttachForProcessId import cCdbWrapper_fAttachForProcessId;
from .cCdbWrapper_fAttachForProcessExecutableNames import cCdbWrapper_fAttachForProcessExecutableNames;
from .cCdbWrapper_fCdbInterruptOnTimeoutHelperThread import cCdbWrapper_fCdbInterruptOnTimeoutHelperThread;
from .cCdbWrapper_fCdbStdErrHelperThread import cCdbWrapper_fCdbStdErrHelperThread;
from .cCdbWrapper_fCdbStdInOutHelperThread import cCdbWrapper_fCdbStdInOutHelperThread;
from .cCdbWrapper_fCleanupHelperThread import cCdbWrapper_fCleanupHelperThread;
from .cCdbWrapper_fClearTimeout import cCdbWrapper_fClearTimeout;
from .cCdbWrapper_fHandleApplicationProcessTermination import cCdbWrapper_fHandleApplicationProcessTermination;
from .cCdbWrapper_fHandleNewApplicationProcess import cCdbWrapper_fHandleNewApplicationProcess;
from .cCdbWrapper_fHandleNewUtilityProcess import cCdbWrapper_fHandleNewUtilityProcess;
from .cCdbWrapper_fInterruptApplicationExecution import cCdbWrapper_fInterruptApplicationExecution;
from .cCdbWrapper_foSetTimeout import cCdbWrapper_foSetTimeout;
from .cCdbWrapper_foStartApplicationProcess import cCdbWrapper_foStartApplicationProcess;
from .cCdbWrapper_fRemoveBreakpoint import cCdbWrapper_fRemoveBreakpoint;
from .cCdbWrapper_fRunTimeoutCallbacks import cCdbWrapper_fRunTimeoutCallbacks;
from .cCdbWrapper_fSelectProcessAndThread import cCdbWrapper_fSelectProcessAndThread;
from .cCdbWrapper_fsHTMLEncode import cCdbWrapper_fsHTMLEncode;
from .cCdbWrapper_fStartUWPApplication import cCdbWrapper_fStartUWPApplication;
from .cCdbWrapper_fTerminateUWPApplication import cCdbWrapper_fTerminateUWPApplication;
from .cCdbWrapper_fuAddBreakpointForAddress import cCdbWrapper_fuAddBreakpointForAddress;
from .cCdbWrapper_fuGetValueForRegister import cCdbWrapper_fuGetValueForRegister;
from .cCollateralBugHandler import cCollateralBugHandler;
from .cExcessiveCPUUsageDetector import cExcessiveCPUUsageDetector;
from .cHelperThread import cHelperThread;
from .cUWPApplication import cUWPApplication;
from .cVerifierStopDetector import cVerifierStopDetector;
from .dxConfig import dxConfig;
import mProductDetails;
from mWindowsAPI import cConsoleProcess, fsGetPythonISA;
from mMultiThreading import cLock;

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
    sCdbISA, # Which version of cdb should be used to debug this application? ("x86" or "x64")
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
    if sCdbISA:
      assert not (sCdbISA == "x64" and fsGetPythonISA() == "x86"), \
          "You cannot use a 64-bit version of cdb.exe when you are using a 32-bit version of Python.";
      oCdbWrapper.sCdbISA = sCdbISA;
    else:
      oCdbWrapper.sCdbISA = fsGetPythonISA();
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
    oCdbWrapper.oEventCallbacksLock = cLock();
    oCdbWrapper.dafEventCallbacks_by_sEventName = {
      # These are the names of all the events that cCdbWrapper can throw. If it's not in the list, you cannot use it in
      # `fAddEventCallback`, `fRemoveEventCallback`, or `fbFireEvent`. The same event names are used by cBugId, but
      # any
      "Application resumed": [], # ()
      "Application running": [], # ()
      "Application debug output": [], # (cProcess oProcess, str[] asOutput)
      "Application stderr output": [], # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Application stdout output": [], # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Application suspended": [], # (str sReason)
      "Bug report": [], # (cBugReport oBugReport)
      "Cdb stderr output": [], # (str sOutput)
      "Cdb stdin input": [], # (str sInput)
      "Cdb stdout output": [], # (str sOutput)
      "Failed to apply application memory limits": [], # (cProcess oProcess)
      "Failed to apply process memory limits": [], # (cProcess oProcess)
      "Failed to debug application": [], # (str sReason)
      "Finished": [], # ()
      "Internal exception": [], # (Exception oException, traceback oTraceBack)
      "Log message": [], # (str sDescription, dict dxData)
      "License errors": [], # (str[] asErrors)
      "License warnings": [], # (str[] asWarnings)
      "Page heap not enabled": [], # (cProcess oProcess, bool bPreventable)
      "Cdb ISA not ideal": [], # (cProcess oProcess, str sCdbISA, bool bPreventable)
      "Process attached": [], # (cProcess oProcess)
      "Process started": [], # (mWindowsAPI.cConsoleProcess oConsoleProcess)
      "Process terminated": [], #(cProcess oProcess)
    };

  
    # This is where we keep track of the threads that are executing (for debug purposes):
    oCdbWrapper.aoActiveHelperThreads = [];
    # Get the cdb binary path
    oCdbWrapper.sDebuggingToolsPath = dxConfig["sDebuggingToolsPath_%s" % oCdbWrapper.sCdbISA];
    assert oCdbWrapper.sDebuggingToolsPath, \
        "No %s Debugging Tools for Windows path found" % oCdbWrapper.sCdbISA;
    assert os.path.isdir(oCdbWrapper.sDebuggingToolsPath), \
        "%s Debugging Tools for Windows path %s not found" % (oCdbWrapper.sCdbISA, oCdbWrapper.sDebuggingToolsPath);
    
    oCdbWrapper.doProcess_by_uId = {};
    oCdbWrapper.doConsoleProcess_by_uId = {};
    oCdbWrapper.oCdbCurrentProcess = None; # The current process id in cdb's context
    oCdbWrapper.oCdbCurrentWindowsAPIThread = None; # The current thread id in cdb's context
    oCdbWrapper.sCdbCurrentISA = None; # The ISA cdb is debugging the current process in (can differ from the process' ISA!)
    # Initialize some variables
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
    oCdbWrapper.duAddress_by_uBreakpointId = {};
    oCdbWrapper.dfCallback_by_uBreakpointId = {};
    oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId = {};
    # You can tell BugId to check for excessive CPU usage among all the threads running in the application.
    # See fSetCheckForExcessiveCPUUsageTimeout and cExcessiveCPUUsageDetector.py for more information
    oCdbWrapper.oExcessiveCPUUsageDetector = cExcessiveCPUUsageDetector(oCdbWrapper);
    # Keep track of timeouts that should fire at some point in the future and timeouts that should fire now.
    oCdbWrapper.aoTimeouts = [];
    oCdbWrapper.uUtilityInterruptThreadId = None; # Will be set to the thread id in which we triggered an AV to
                                                  # interrupt the application.
    # Two locks, one of which is always locked while the application is executing. 
    oCdbWrapper.bApplicationIsRunning = False;
    # Keep track of how long the application has been running, used for timeouts (see foSetTimeout, fCdbStdInOutThread
    # and fCdbInterruptOnTimeoutThread for details. The debugger can tell is what time it thinks it is before we start
    # and resume the application as well as what time it thinks it was when an exception happened. The difference is
    # used to calculate how long the application has been running. We cannot simply use time.clock() before start/
    # resuming and at the time an event is handled as the debugger may take quite some time processing an event before
    # we can call time.clock(): this time would incorrectly be added to the time the application has spent running.
    # However, while the application is running, we cannot ask the debugger what time it thinks it is, so we have to 
    # rely on time.clock(). Hence, both values are tracked.
    oCdbWrapper.oApplicationTimeLock = cLock();
    oCdbWrapper.nConfirmedApplicationRunTime = 0; # Total time spent running before last interruption
    oCdbWrapper.nApplicationResumeDebuggerTime = None;  # debugger time at the moment the application was last resumed
    oCdbWrapper.nApplicationResumeTime = None;          # time.clock() at the moment the application was last resumed
    
    oCdbWrapper.oCollateralBugHandler = cCollateralBugHandler(oCdbWrapper, uMaximumNumberOfBugs);
    
    # Create VERIFIER STOP and Asan ERROR detectors. The later also needs to be called when a Breakpoint exception
    # happens in order to report it (the former reports the error as soon as it is detected in applicationm debug
    # output).
    cVerifierStopDetector(oCdbWrapper);
    oCdbWrapper.oASanErrorDetector = cASanErrorDetector(oCdbWrapper);
    
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      def fWriteLogMessageToReport(sMessage, dsData = None):
        sData = dsData and ", ".join(["%s: %s" % (sName, sValue) for (sName, sValue) in dsData.items()]);
        oCdbWrapper.sLogHTML += "<span class=\"LogMessage\">%s%s</span><br/>\n" % \
            (oCdbWrapper.fsHTMLEncode(sMessage), sData and " (%s)" % oCdbWrapper.fsHTMLEncode(sData) or "");
      oCdbWrapper.fAddEventCallback("Log message", fWriteLogMessageToReport);
  
  @property
  def bUsingSymbolServers(oCdbWrapper):
    return len(oCdbWrapper.asSymbolServerURLs) > 0;
  
  def fStart(oCdbWrapper):
    global guSymbolOptions;
    oLicenseCollection = mProductDetails.foGetLicenseCollectionForAllLoadedProducts();
    (asLicenseErrors, asLicenseWarnings) = oLicenseCollection.ftasGetLicenseErrorsAndWarnings();
    if asLicenseErrors:
      if not oCdbWrapper.fbFireEvent("License errors", asLicenseErrors):
        print "You do not have a valid, active license for cBugId:\r\n%s" % "\r\n".join(asLicenseErrors);
        os._exit(5);
      return;
    if asLicenseWarnings:
      oCdbWrapper.fbFireEvent("License warnings", asLicenseWarnings);
    # Create a thread that interacts with the debugger to debug the application
    oCdbWrapper.oCdbStdInOutHelperThread = cHelperThread(oCdbWrapper, "cdb.exe stdin/out thread", oCdbWrapper.fCdbStdInOutHelperThread, bVital = True);
    # Create a thread that reads stderr output and shows it in the console
    oCdbWrapper.oCdbStdErrHelperThread = cHelperThread(oCdbWrapper, "cdb.exe stderr thread", oCdbWrapper.fCdbStdErrHelperThread, bVital = True);
    # Create a thread that waits for the debugger to terminate and cleans up after it.
    oCdbWrapper.oCleanupHelperThread = cHelperThread(oCdbWrapper, "cleanup thread", oCdbWrapper.fCleanupHelperThread, bVital = True);
    # Create a thread that waits for a certain amount of time while cdb is running and then interrupts it.
    oCdbWrapper.oInterruptOnTimeoutHelperThread = cHelperThread(oCdbWrapper, "cdb.exe interrupt on timeout thread", oCdbWrapper.fCdbInterruptOnTimeoutHelperThread);
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
    sCdbBinaryPath = os.path.join(oCdbWrapper.sDebuggingToolsPath, "cdb.exe");
    assert os.path.isfile(sCdbBinaryPath), \
        "%s Debugging Tools for Windows cdb.exe file %s not found" % (oCdbWrapper.sCdbISA, sCdbBinaryPath);
    oCdbWrapper.oCdbConsoleProcess = cConsoleProcess.foCreateForBinaryPathAndArguments(
      sBinaryPath = sCdbBinaryPath,
      asArguments = asArguments,
    );
    assert oCdbWrapper.oCdbConsoleProcess, \
        "Cannot find %s!" % sCdbBinaryPath;
    oCdbWrapper.oCdbStdInOutHelperThread.fStart();
    oCdbWrapper.oCdbStdErrHelperThread.fStart();
    oCdbWrapper.oCleanupHelperThread.fStart();
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
      oCdbWrapper.fAttachForProcessId(uProcessId, bMustBeResumed = True);
  
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
    if oCdbWrapper.bApplicationIsRunning:
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
  def fSetCheckForExcessiveCPUUsageTimeout(oCdbWrapper, nTimeoutInSeconds):
    oCdbWrapper.oExcessiveCPUUsageDetector.fStartTimeout(nTimeoutInSeconds);
  def fCheckForExcessiveCPUUsage(oCdbWrapper, fCallback):
    oCdbWrapper.oExcessiveCPUUsageDetector.fCheckForExcessiveCPUUsage(fCallback);
  
  @property
  def nApplicationRunTime(oCdbWrapper):
    # This can be exact (when the application is suspended) or an estimate (when the application is running).
    if not oCdbWrapper.bApplicationIsRunning:
      # Fast and exact path.
      return oCdbWrapper.nConfirmedApplicationRunTime;
    oCdbWrapper.oApplicationTimeLock.fAcquire();
    try:
      return oCdbWrapper.nConfirmedApplicationRunTime + time.clock() - oCdbWrapper.nApplicationResumeTime;
    finally:
      oCdbWrapper.oApplicationTimeLock.fRelease();
  
  # Breakpoints
  def fuAddBreakpointForAddress(oCdbWrapper, uAddress, fCallback, uProcessId, uThreadId = None, sCommand = None):
    return cCdbWrapper_fuAddBreakpointForAddress(oCdbWrapper, uAddress, fCallback, uProcessId, uThreadId, sCommand);
  def fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments):
    return cCdbWrapper_fRemoveBreakpoint(oCdbWrapper, *axArguments, **dxArguments);
  
  # Timeouts/interrupt
  def foSetTimeout(oCdbWrapper, sDescription, nTimeoutInSeconds, fCallback, *axCallbackArguments):
    return cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, nTimeoutInSeconds, fCallback, *axCallbackArguments);
  def fInterrupt(oCdbWrapper, sDescription, fCallback, *axCallbackArguments):
    # An interrupt == an immediate timeout
    cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, 0, fCallback, *axCallbackArguments);
  def fClearTimeout(oCdbWrapper, oTimeout):
    return cCdbWrapper_fClearTimeout(oCdbWrapper, oTimeout);
  def fCdbInterruptOnTimeoutHelperThread(oCdbWrapper):
    return cCdbWrapper_fCdbInterruptOnTimeoutHelperThread(oCdbWrapper);
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
    return cCdbWrapper_fInterruptApplicationExecution(oCdbWrapper);
  
  # stdin/out/err handling threads
  def fCdbStdInOutHelperThread(oCdbWrapper):
    return cCdbWrapper_fCdbStdInOutHelperThread(oCdbWrapper);
  def fCdbStdErrHelperThread(oCdbWrapper):
    return cCdbWrapper_fCdbStdErrHelperThread(oCdbWrapper);
  def fCleanupHelperThread(oCdbWrapper):
    return cCdbWrapper_fCleanupHelperThread(oCdbWrapper);
  def fApplicationStdOutOrErrHelperThread(oCdbWraper, oConsoleProcess, oStdOutOrErrPipe):
    return cCdbWrapper_fApplicationStdOutOrErrHelperThread(oCdbWraper, oConsoleProcess, oStdOutOrErrPipe);
  
  # Event handling
  def fAddEventCallback(oCdbWrapper, sEventName, fCallback):
    assert sEventName in oCdbWrapper.dafEventCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    oCdbWrapper.oEventCallbacksLock.fAcquire();
    try:
      oCdbWrapper.dafEventCallbacks_by_sEventName[sEventName].append(fCallback);
    finally:
      oCdbWrapper.oEventCallbacksLock.fRelease();
  def fRemoveEventCallback(oCdbWrapper, sEventName, fCallback):
    assert sEventName in oCdbWrapper.dafEventCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    oCdbWrapper.oEventCallbacksLock.fAcquire();
    try:
      oCdbWrapper.dafEventCallbacks_by_sEventName[sEventName].remove(fCallback);
    finally:
      oCdbWrapper.oEventCallbacksLock.fRelease();
  def fbFireEvent(oCdbWrapper, sEventName, *axCallbackArguments):
    assert sEventName in oCdbWrapper.dafEventCallbacks_by_sEventName, \
        "Unknown event name %s" % repr(sEventName);
    oCdbWrapper.oEventCallbacksLock.fAcquire();
    try:
      afCallbacks = oCdbWrapper.dafEventCallbacks_by_sEventName[sEventName][:];
    finally:
      oCdbWrapper.oEventCallbacksLock.fRelease();
    for fCallback in afCallbacks:
      fCallback(*axCallbackArguments);
    return len(afCallbacks) > 0;
  
  # Start/attach to processes
  def foStartApplicationProcess(oCdbWrapper, sBinaryPath, asArguments):
    return cCdbWrapper_foStartApplicationProcess(oCdbWrapper, sBinaryPath, asArguments);
  def fAttachForProcessId(oCdbWrapper, uProcessId, bMustBeResumed = False):
    return cCdbWrapper_fAttachForProcessId(oCdbWrapper, uProcessId, bMustBeResumed);
  def fAttachForProcessExecutableNames(oCdbWrapper, *asBinaryNames):
    return cCdbWrapper_fAttachForProcessExecutableNames(oCdbWrapper, *asBinaryNames);
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
  
  def fuGetValueForRegister(oCdbWrapper, sRegister, sComment):
    return cCdbWrapper_fuGetValueForRegister(oCdbWrapper, sRegister, sComment);