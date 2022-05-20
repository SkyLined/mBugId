import itertools, time;

import mProductDetails;
from mWindowsAPI import cConsoleProcess, cProcess, fsGetPythonISA;
from mMultiThreading import cLock, cWithCallbacks;
from mFileSystemItem import cFileSystemItem;
from mNotProvided import *;

from ..cASanErrorDetector import cASanErrorDetector;
from ..cCollateralBugHandler import cCollateralBugHandler;
from ..cExcessiveCPUUsageDetector import cExcessiveCPUUsageDetector;
from ..cVerifierStopDetector import cVerifierStopDetector;
from ..dxConfig import dxConfig;
from ..mCP437 import fsCP437HTMLFromString;

from .cCdbWrapper_cCdbStoppedException import cCdbWrapper_cCdbStoppedException;
from .cCdbWrapper_cEndOfCommandOutputMarkerMissingException import cCdbWrapper_cEndOfCommandOutputMarkerMissingException;
from .cCdbWrapper_cHelperThread import cCdbWrapper_cHelperThread;
from .cCdbWrapper_fAllocateReserveMemoryIfNeeded import cCdbWrapper_fAllocateReserveMemoryIfNeeded;
from .cCdbWrapper_fApplicationStdOutOrErrHelperThread import cCdbWrapper_fApplicationStdOutOrErrHelperThread;
from .cCdbWrapper_fasbExecuteCdbCommand import cCdbWrapper_fasbExecuteCdbCommand;
from .cCdbWrapper_fasbReadOutput import cCdbWrapper_fasbReadOutput;
from .cCdbWrapper_fAttachCdbToProcessForId import cCdbWrapper_fAttachCdbToProcessForId;
from .cCdbWrapper_fCdbInterruptOnTimeoutHelperThread import cCdbWrapper_fCdbInterruptOnTimeoutHelperThread;
from .cCdbWrapper_fCdbStdErrHelperThread import cCdbWrapper_fCdbStdErrHelperThread;
from .cCdbWrapper_fCdbStdInOutHelperThread import cCdbWrapper_fCdbStdInOutHelperThread;
from .cCdbWrapper_fCleanupHelperThread import cCdbWrapper_fCleanupHelperThread;
from .cCdbWrapper_fClearTimeout import cCdbWrapper_fClearTimeout;
from .cCdbWrapper_fHandleCurrentApplicationProcessTermination import cCdbWrapper_fHandleCurrentApplicationProcessTermination;
from .cCdbWrapper_fHandleAttachedToApplicationProcess import cCdbWrapper_fHandleAttachedToApplicationProcess;
from .cCdbWrapper_fHandleAttachedToUtilityProcess import cCdbWrapper_fHandleAttachedToUtilityProcess;
from .cCdbWrapper_fHandleBreakpoint import cCdbWrapper_fHandleBreakpoint;
from .cCdbWrapper_fHandleDebugOutputFromApplication import cCdbWrapper_fHandleDebugOutputFromApplication;
from .cCdbWrapper_fHandleExceptionInUtilityProcess import cCdbWrapper_fHandleExceptionInUtilityProcess;
from .cCdbWrapper_fInterruptApplicationExecution import cCdbWrapper_fInterruptApplicationExecution;
from .cCdbWrapper_foSetTimeout import cCdbWrapper_foSetTimeout;
from .cCdbWrapper_foStartApplicationProcess import cCdbWrapper_foStartApplicationProcess;
from .cCdbWrapper_fQueueAttachForProcessExecutableNames import cCdbWrapper_fQueueAttachForProcessExecutableNames;
from .cCdbWrapper_fQueueAttachForProcessId import cCdbWrapper_fQueueAttachForProcessId;
from .cCdbWrapper_fRemoveBreakpoint import cCdbWrapper_fRemoveBreakpoint;
from .cCdbWrapper_fRunTimeoutCallbacks import cCdbWrapper_fRunTimeoutCallbacks;
from .cCdbWrapper_fSaveDumpToFile import cCdbWrapper_fSaveDumpToFile;
from .cCdbWrapper_fSelectProcessIdAndThreadId import cCdbWrapper_fSelectProcessIdAndThreadId;
from .cCdbWrapper_fStartUWPApplication import cCdbWrapper_fStartUWPApplication;
from .cCdbWrapper_ftbHandleLastCdbEvent import cCdbWrapper_ftbHandleLastCdbEvent;
from .cCdbWrapper_fTerminateUWPApplication import cCdbWrapper_fTerminateUWPApplication;
from .cCdbWrapper_fuAddBreakpointForProcessIdAndAddress import cCdbWrapper_fuAddBreakpointForProcessIdAndAddress;
from .cCdbWrapper_fuGetValueForRegister import cCdbWrapper_fuGetValueForRegister;
from .cCdbWrapper_fUpdateCdbISA import cCdbWrapper_fUpdateCdbISA;

# Remaining local modules are load JIT to mitigate loops.

gnDeadlockTimeoutInSeconds = 1;

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

class cCdbWrapper(cWithCallbacks):
  cCdbStoppedException = cCdbWrapper_cCdbStoppedException;
  cEndOfCommandOutputMarkerMissingException = cCdbWrapper_cEndOfCommandOutputMarkerMissingException;
  
  def __init__(oCdbWrapper,
    sCdbISA, # Which version of cdb should be used to debug this application? ("x86" or "x64")
    s0ApplicationBinaryPath,
    a0uApplicationProcessIds,
    u0JITDebuggerEventId,
    o0UWPApplication,
    asApplicationArguments,
    asLocalSymbolPaths,
    azsSymbolCachePaths, 
    azsSymbolServerURLs,
    d0sURLTemplate_by_srSourceFilePath,
    bGenerateReportHTML,        
    u0ProcessMaxMemoryUse,
    u0TotalMaxMemoryUse,
    u0MaximumNumberOfBugs,
    f0iCollateralInteractiveAskForValue,
  ):
    if sCdbISA:
      assert not (sCdbISA == "x64" and fsGetPythonISA() == "x86"), \
          "You cannot use a 64-bit version of cdb.exe when you are using a 32-bit version of Python.";
      oCdbWrapper.sCdbISA = sCdbISA;
    else:
      oCdbWrapper.sCdbISA = fsGetPythonISA();
    assert s0ApplicationBinaryPath or a0uApplicationProcessIds or o0UWPApplication, \
        "You must provide one of the following: an application command line, a list of process ids or an application package name";
    oCdbWrapper.s0ApplicationBinaryPath = s0ApplicationBinaryPath;
    oCdbWrapper.auApplicationProcessIds = a0uApplicationProcessIds or [];
    oCdbWrapper.auMainProcessIds = oCdbWrapper.auApplicationProcessIds[:];
    oCdbWrapper.u0JITDebuggerEventId = u0JITDebuggerEventId;
    oCdbWrapper.o0UWPApplication = o0UWPApplication;
    oCdbWrapper.bApplicationStarted = False;
    # Keep track of all application processes we start and their stdout/stderr pipes
    # so we can make sure they are all terminated and closed respectively when cBugId
    # is terminated.
    oCdbWrapper.aoApplicationProcesses = [];
    oCdbWrapper.daoApplicationStdOutAndStdErrPipes_by_uProcessId = {};
    oCdbWrapper.daoApplicationStdOutAndStdErrPipeThreads_by_uProcessId = {};
    oCdbWrapper.bUWPApplicationStarted = False;
    oCdbWrapper.bStopping = False;
    oCdbWrapper.asApplicationArguments = asApplicationArguments;
    oCdbWrapper.asLocalSymbolPaths = asLocalSymbolPaths;
    oCdbWrapper.asSymbolCachePaths = fxGetFirstProvidedValue(azsSymbolCachePaths, dxConfig["asDefaultSymbolCachePaths"]);
    oCdbWrapper.asSymbolServerURLs = fxGetFirstProvidedValue(azsSymbolServerURLs, dxConfig["asDefaultSymbolServerURLs"]);
    oCdbWrapper.dsURLTemplate_by_srSourceFilePath = d0sURLTemplate_by_srSourceFilePath or {};
    oCdbWrapper.bGenerateReportHTML = bGenerateReportHTML;
    oCdbWrapper.u0ProcessMaxMemoryUse = u0ProcessMaxMemoryUse;
    oCdbWrapper.u0TotalMaxMemoryUse = u0TotalMaxMemoryUse;
    oCdbWrapper.o0ReservedMemoryVirtualAllocation = None;
    oCdbWrapper.fAddEvents(
      # These are the names of all the events that cCdbWrapper can throw. If it's not in the list, you cannot use it in
      # `fAddCallback`, `fbRemoveCallback`, or `fbFireCallbacks`. The same event names are used by cBugId, but
      # any
      "Application resumed", # ()
      "Application running", # ()
      "Application debug output", # (cProcess oProcess, str[] asOutput)
      "Application stderr output", # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Application stdout output", # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Application suspended", # (str sReason)
      "ASan detected", # ()
      "Bug cannot be ignored", # (str sReason)
      "Bug ignored", # (str, sInstruction, str[] asActions)
      "Bug report", # (cBugReport oBugReport)
      "Cdb command started executing", # (sbCommand, uAttempt, uTries, sb0Comment)
      "Cdb command finished executing", # (sbCommand, uAttempt, uTries, sb0Comment)
      "Cdb stderr output", # (str sOutput)
      "Cdb stdin input", # (str sInput)
      "Cdb stdout output", # (str sOutput)
      "Failed to apply application memory limits", # (cProcess oProcess)
      "Failed to apply process memory limits", # (cProcess oProcess)
      "Failed to debug application", # (str sReason)
      "Finished", # ()
      "Internal exception", # (mMultiThreading.cThread oThread, Exception oException, traceback oTraceBack)
      "Log message", # (str sDescription[, dict d0xData])
      "License errors", # (str[] asErrors)
      "License warnings", # (str[] asWarnings)
      "Page heap not enabled", # (cProcess oProcess, bool bPreventable)
      "Cdb ISA not ideal", # (cProcess oProcess, str sCdbISA, bool bPreventable)
      "Process attached", # (cProcess oProcess)
      "Process started", # (mWindowsAPI.cConsoleProcess oConsoleProcess)
      "Process terminated", #(cProcess oProcess)
    );
    
    # This is where we keep track of the threads that are executing (for debug purposes):
    oCdbWrapper.aoActiveHelperThreads = [];
    # Get the cdb binary path
    oCdbWrapper.sDebuggingToolsPath = dxConfig["sDebuggingToolsPath_%s" % oCdbWrapper.sCdbISA];
    assert oCdbWrapper.sDebuggingToolsPath, \
        "No %s Debugging Tools for Windows path found" % oCdbWrapper.sCdbISA;
    assert cFileSystemItem(oCdbWrapper.sDebuggingToolsPath).fbIsFolder(), \
        "%s Debugging Tools for Windows path %s not found" % (oCdbWrapper.sCdbISA, oCdbWrapper.sDebuggingToolsPath);
    
    oCdbWrapper.doProcess_by_uId = {};
    oCdbWrapper.oCdbCurrentProcess = None; # The current process id in cdb's context
    oCdbWrapper.oCdbCurrentWindowsAPIThread = None; # The current thread id in cdb's context
    oCdbWrapper.sCdbCurrentISA = None; # The ISA cdb is debugging the current process in (can differ from the process' ISA!)
    # Initialize some variables
    if bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML = ""; # Logs stdin/stdout/stderr for the cdb process, grouped by executed command.
      oCdbWrapper.sPromptHTML = None; # Logs cdb prompt to be adde to CdbIOHTML if a command is added.
      if dxConfig["bLogInReport"]:
        oCdbWrapper.sLogHTML = ""; # Logs various events that may be relevant
    oCdbWrapper.bCdbIsRunning = True; # Set to False after cdb terminated, used to terminate the debugger thread.
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
    # used to calculate how long the application has been running. We cannot simply use time.time() before start/
    # resuming and at the time an event is handled as the debugger may take quite some time processing an event before
    # we can call time.time(): this time would incorrectly be added to the time the application has spent running.
    # However, while the application is running, we cannot ask the debugger what time it thinks it is, so we have to 
    # rely on time.time(). Hence, both values are tracked.
    oCdbWrapper.oApplicationTimeLock = cLock(n0DeadlockTimeoutInSeconds = 1);
    oCdbWrapper.nConfirmedApplicationRunTimeInSeconds = 0; # Total time spent running before last interruption
    oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds = None;  # debugger time at the moment the application was last resumed
    oCdbWrapper.nApplicationResumeTimeInSeconds = None;          # time.time() at the moment the application was last resumed
    
    oCdbWrapper.oCollateralBugHandler = cCollateralBugHandler(
      oCdbWrapper,
      u0MaximumNumberOfBugs,
      f0iCollateralInteractiveAskForValue,
    );
    
    # Create VERIFIER STOP and Asan ERROR detectors. The later also needs to be called when a Breakpoint exception
    # happens in order to report it (the former reports the error as soon as it is detected in applicationm debug
    # output).
    cVerifierStopDetector(oCdbWrapper);
    oCdbWrapper.oASanErrorDetector = cASanErrorDetector(oCdbWrapper);
    
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      def fWriteLogMessageToReport(oCdbWrapper, sMessage, d0xData = None):
        s0Data = None if d0xData is None else (
          "{%s}" % ", ".join(["%s: %s" % (repr(sName), repr(sValue)) for (sName, sValue) in d0xData.items()])
        );
        oCdbWrapper.sLogHTML += "<span class=\"LogMessage\">%s%s</span><br/>\n" % (
          fsCP437HTMLFromString(sMessage),
          s0Data and " %s" % fsCP437HTMLFromString(s0Data) or "",
        );
      oCdbWrapper.fAddCallback("Log message", fWriteLogMessageToReport);
  
  def foCreateHelperThread(oSelf, *txArguments, **dxArguments):
    return cCdbWrapper_cHelperThread(oSelf, *txArguments, **dxArguments);
  
  @property
  def bUsingSymbolServers(oSelf):
    return len(oSelf.asSymbolServerURLs) > 0;
  
  def fLogMessage(oSelf, sMessage, d0xData = None):
    oSelf.fbFireCallbacks("Log message", sMessage, d0xData);
  
  def fStart(oCdbWrapper):
    global guSymbolOptions;
    oLicenseCollection = mProductDetails.foGetLicenseCollectionForAllLoadedProducts();
    (asLicenseErrors, asLicenseWarnings) = oLicenseCollection.ftasGetLicenseErrorsAndWarnings();
    if asLicenseErrors:
      assert oCdbWrapper.fbFireCallbacks("License errors", asLicenseErrors), \
          "You do not have a valid, active license for cBugId:\r\n%s" % "\r\n".join(asLicenseErrors);
      oCdbWrapper.fStop();
      return False;
    if asLicenseWarnings:
      oCdbWrapper.fbFireCallbacks("License warnings", asLicenseWarnings);
    # If we are starting a UWP application, make sure it exists:
    if oCdbWrapper.o0UWPApplication:
      if not oCdbWrapper.o0UWPApplication.bPackageExists:
        sMessage = "UWP Application package \"%s\" does not exist." % oCdbWrapper.o0UWPApplication.sPackageName;
        assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
            sMessage;
        oCdbWrapper.fStop();
        return;
      elif not oCdbWrapper.o0UWPApplication.bIdExists:
        sMessage = "UWP Application id \"%s\" does not exist in package \"%s\" (valid applications: %s)." % \
            (oCdbWrapper.o0UWPApplication.sApplicationId, oCdbWrapper.o0UWPApplication.sPackageName, ", ".join([
              "\"%s\"" % sApplicationId for sApplicationId in oCdbWrapper.o0UWPApplication.asApplicationIds
            ]));
        assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
            sMessage;
        oCdbWrapper.fStop();
        return;
    # Create a thread that interacts with the debugger to debug the application
    oCdbWrapper.oCdbStdInOutHelperThread = oCdbWrapper.foCreateHelperThread("cdb.exe stdin/out thread", oCdbWrapper.fCdbStdInOutHelperThread, bVital = True);
    # Create a thread that reads stderr output and shows it in the console
    oCdbWrapper.oCdbStdErrHelperThread = oCdbWrapper.foCreateHelperThread("cdb.exe stderr thread", oCdbWrapper.fCdbStdErrHelperThread, bVital = True);
    # Create a thread that waits for the debugger to terminate and cleans up after it.
    oCdbWrapper.oCleanupHelperThread = oCdbWrapper.foCreateHelperThread("cleanup thread", oCdbWrapper.fCleanupHelperThread, bVital = True);
    # Create a thread that waits for a certain amount of time while cdb is running and then interrupts it.
    oCdbWrapper.oInterruptOnTimeoutHelperThread = oCdbWrapper.foCreateHelperThread("cdb.exe interrupt on timeout thread", oCdbWrapper.fCdbInterruptOnTimeoutHelperThread);
    # Find out where cdb.exe is at:
    oCdbBinaryFile = cFileSystemItem(oCdbWrapper.sDebuggingToolsPath).foGetChild("cdb.exe");
    assert oCdbBinaryFile.fbIsFile(), \
        "%s Debugging Tools for Windows cdb.exe file %s not found" % (oCdbWrapper.sCdbISA, oCdbBinaryFile.sPath);
    # We first start a utility process that we can use to trigger breakpoints in, so we can distinguish them from
    # breakpoints triggered in the target application. For this we'll start a copy of cdb.exe, suspended, since we
    # alreadyknow the path to the binary. We do not need to provide any arguments since the application will be
    # suspended and not do anything after initialization.
    oCdbWrapper.fLogMessage("Starting utility process...");
    oCdbWrapper.oUtilityProcess = cProcess.foCreateForBinaryPath(
      sBinaryPath = oCdbBinaryFile.sPath,
      bHidden = True,
      bSuspended = True,
    );
    oCdbWrapper.fLogMessage("Started utility process (0x%X)." % oCdbWrapper.oUtilityProcess.uId);
    if oCdbWrapper.s0ApplicationBinaryPath is not None:
      # If a process must be started, add it to the command line.
      assert not oCdbWrapper.auApplicationProcessIds, \
          "Cannot start a process and attach to processes at the same time";
    elif oCdbWrapper.o0UWPApplication:
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
    
    if oCdbWrapper.u0JITDebuggerEventId is None:
      # Attach directly to the utility process and queue attaching to other
      # processes the user wants us to attach to if we're not JIT debugging.
      asAttachAndOptionallyHandleExceptionArguments = [
        "-p", str(oCdbWrapper.oUtilityProcess.uId),
      ];
      oCdbWrapper.auProcessIdsPendingAttach = [oCdbWrapper.oUtilityProcess.uId] + oCdbWrapper.auApplicationProcessIds;
    else:
      # If we are JIT debugging: attach to the process in which an exception
      # happened and queue attaching to the utility process.
      assert len(oCdbWrapper.auApplicationProcessIds) == 1, \
          "Cannot attach to multiple processes while JIT debugging!";
      asAttachAndOptionallyHandleExceptionArguments = [
        "-p", str(oCdbWrapper.auApplicationProcessIds[0]), "-e", str(oCdbWrapper.u0JITDebuggerEventId),
      ];
      oCdbWrapper.auProcessIdsPendingAttach = oCdbWrapper.auApplicationProcessIds + [oCdbWrapper.oUtilityProcess.uId];
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
    ] or []) + (
      asAttachAndOptionallyHandleExceptionArguments
    );
    oCdbWrapper.oCdbConsoleProcess = cConsoleProcess.foCreateForBinaryPathAndArguments(
      sBinaryPath = oCdbBinaryFile.sPath,
      asArguments = asArguments,
    );
    oCdbWrapper.fLogMessage("Started cdb.exe", {
      "Command line components": [oCdbBinaryFile.sPath] + asArguments,
    });
    
    oCdbWrapper.oCdbStdInOutHelperThread.fStart();
    oCdbWrapper.oCdbStdErrHelperThread.fStart();
    oCdbWrapper.oCleanupHelperThread.fStart();
    # If we need to start a binary for this application, do so:
    if oCdbWrapper.s0ApplicationBinaryPath:
      oMainConsoleProcess = oCdbWrapper.foStartApplicationProcess(
        oCdbWrapper.s0ApplicationBinaryPath,
        oCdbWrapper.asApplicationArguments
      );
      if oMainConsoleProcess is None:
        oCdbWrapper.fTerminate();
        return;
      oCdbWrapper.auMainProcessIds.append(oMainConsoleProcess.uId);
    return;
  
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
      assert not oCdbConsoleProcess or not oCdbConsoleProcess.bIsRunning, \
          "cCdbWrapper is being destroyed while cdb.exe is still running.";
  
  # Select process/thread
  def fSelectProcessId(oCdbWrapper, uProcessId):
    return oCdbWrapper.fSelectProcessIdAndThreadId(uProcessId = uProcessId);
  def fSelectThreadId(oCdbWrapper, uThreadId):
    return oCdbWrapper.fSelectProcessIdAndThreadId(uThreadId = uThreadId);
  def fSelectProcessIdAndThreadId(oCdbWrapper, uProcessId = None, uThreadId = None):
    return cCdbWrapper_fSelectProcessIdAndThreadId(oCdbWrapper, uProcessId, uThreadId);
  
  # Excessive CPU usage
  def fSetCheckForExcessiveCPUUsageTimeout(oCdbWrapper, nTimeoutInSeconds):
    oCdbWrapper.oExcessiveCPUUsageDetector.fStartTimeout(nTimeoutInSeconds);
  def fCheckForExcessiveCPUUsage(oCdbWrapper, fCallback):
    oCdbWrapper.oExcessiveCPUUsageDetector.fCheckForExcessiveCPUUsage(fCallback);
  
  @property
  def nApplicationRunTimeInSeconds(oCdbWrapper):
    # This can be exact (when the application is suspended) or an estimate (when the application is running).
    if not oCdbWrapper.bApplicationIsRunning:
      # Fast and exact path.
      return oCdbWrapper.nConfirmedApplicationRunTimeInSeconds;
    oCdbWrapper.oApplicationTimeLock.fAcquire();
    try:
      return oCdbWrapper.nConfirmedApplicationRunTimeInSeconds + time.time() - oCdbWrapper.nApplicationResumeTimeInSeconds;
    finally:
      oCdbWrapper.oApplicationTimeLock.fRelease();
  
  # `fInterrupt` == `foSetTimeout` for 0 second (immediate)
  def fInterrupt(oCdbWrapper, sDescription, f0Callback = None, txCallbackArguments = tuple()):
    oCdbWrapper.foSetTimeout(sDescription, 0, f0Callback, txCallbackArguments);
  
  fRunTimeoutCallbacks = cCdbWrapper_fRunTimeoutCallbacks;
  fasbReadOutput = cCdbWrapper_fasbReadOutput;
  fAllocateReserveMemoryIfNeeded = cCdbWrapper_fAllocateReserveMemoryIfNeeded;
  fApplicationStdOutOrErrHelperThread = cCdbWrapper_fApplicationStdOutOrErrHelperThread;
  fasbExecuteCdbCommand = cCdbWrapper_fasbExecuteCdbCommand;
  fAttachCdbToProcessForId = cCdbWrapper_fAttachCdbToProcessForId;
  fCdbInterruptOnTimeoutHelperThread = cCdbWrapper_fCdbInterruptOnTimeoutHelperThread;
  fCdbStdInOutHelperThread = cCdbWrapper_fCdbStdInOutHelperThread;
  fCdbStdErrHelperThread = cCdbWrapper_fCdbStdErrHelperThread;
  fCleanupHelperThread = cCdbWrapper_fCleanupHelperThread;
  fClearTimeout = cCdbWrapper_fClearTimeout;
  fHandleAttachedToApplicationProcess = cCdbWrapper_fHandleAttachedToApplicationProcess;
  fHandleAttachedToUtilityProcess = cCdbWrapper_fHandleAttachedToUtilityProcess;
  fHandleCurrentApplicationProcessTermination = cCdbWrapper_fHandleCurrentApplicationProcessTermination;
  fHandleBreakpoint = cCdbWrapper_fHandleBreakpoint;
  fHandleDebugOutputFromApplication = cCdbWrapper_fHandleDebugOutputFromApplication;
  fHandleExceptionInUtilityProcess = cCdbWrapper_fHandleExceptionInUtilityProcess;
  fInterruptApplicationExecution = cCdbWrapper_fInterruptApplicationExecution;
  foSetTimeout = cCdbWrapper_foSetTimeout;
  foStartApplicationProcess = cCdbWrapper_foStartApplicationProcess;
  fQueueAttachForProcessId = cCdbWrapper_fQueueAttachForProcessId;
  fQueueAttachForProcessExecutableNames = cCdbWrapper_fQueueAttachForProcessExecutableNames;
  fRemoveBreakpoint = cCdbWrapper_fRemoveBreakpoint;
  fSaveDumpToFile = cCdbWrapper_fSaveDumpToFile;
  fStartUWPApplication = cCdbWrapper_fStartUWPApplication;
  ftbHandleLastCdbEvent = cCdbWrapper_ftbHandleLastCdbEvent;
  fTerminateUWPApplication = cCdbWrapper_fTerminateUWPApplication;
  fuAddBreakpointForProcessIdAndAddress = cCdbWrapper_fuAddBreakpointForProcessIdAndAddress;
  fuGetValueForRegister = cCdbWrapper_fuGetValueForRegister;
  fUpdateCdbISA = cCdbWrapper_fUpdateCdbISA;

