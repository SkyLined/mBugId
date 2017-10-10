import itertools, json, os, re, subprocess, sys, threading, time;
from cCdbWrapper_fasExecuteCdbCommand import cCdbWrapper_fasExecuteCdbCommand;
from cCdbWrapper_fAskCdbToInterruptApplication import cCdbWrapper_fAskCdbToInterruptApplication;
from cCdbWrapper_fasReadOutput import cCdbWrapper_fasReadOutput;
from cCdbWrapper_fAttachToProcessesForExecutableNames import cCdbWrapper_fAttachToProcessesForBinaryNames;
from cCdbWrapper_f_Breakpoint import cCdbWrapper_fuAddBreakpoint, cCdbWrapper_fRemoveBreakpoint;
from cCdbWrapper_fCdbCleanupThread import cCdbWrapper_fCdbCleanupThread;
from cCdbWrapper_fCdbStdErrThread import cCdbWrapper_fCdbStdErrThread;
from cCdbWrapper_fCdbStdInOutThread import cCdbWrapper_fCdbStdInOutThread;
from cCdbWrapper_fsHTMLEncode import cCdbWrapper_fsHTMLEncode;
from cCdbWrapper_f_Timeout import cCdbWrapper_foSetTimeout, cCdbWrapper_fClearTimeout;
from cExcessiveCPUUsageDetector import cExcessiveCPUUsageDetector;
from cUWPApplication import cUWPApplication;
from dxConfig import dxConfig;
from fbTerminateProcessForId import fbTerminateProcessForId;
from sOSISA import sOSISA;

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
    sApplicationPackageName,
    sApplicationId,
    asApplicationArguments,
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
    fStdInInputCallback,                      # called whenever a line of input is sent to stdin
    fStdOutOutputCallback,                    # called whenever a line of output is read from stdout
    fStdErrOutputCallback,                    # called whenever a line of output is read from stderr
    fNewProcessCallback,                      # called whenever there is a new process.
  ):
    oCdbWrapper.aoInternalExceptions = [];
    oCdbWrapper.sCdbISA = sCdbISA or sOSISA;
    assert sum([sApplicationBinaryPath and 1 or 0, auApplicationProcessIds and 1 or 0, sApplicationPackageName and 1 or 0]), \
        "You must provide one of the following: an application command line, a list of process ids or an application package name";
    oCdbWrapper.sApplicationBinaryPath = sApplicationBinaryPath;
    oCdbWrapper.oUWPApplication = sApplicationPackageName and cUWPApplication(sApplicationPackageName, sApplicationId) or None;
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
    oCdbWrapper.fFailedToDebugApplicationCallback = fFailedToDebugApplicationCallback;
    oCdbWrapper.fApplicationRunningCallback = fApplicationRunningCallback;
    oCdbWrapper.fApplicationSuspendedCallback = fApplicationSuspendedCallback;
    oCdbWrapper.fApplicationResumedCallback = fApplicationResumedCallback;
    oCdbWrapper.fMainProcessTerminatedCallback = fMainProcessTerminatedCallback;
    oCdbWrapper.fInternalExceptionCallback = fInternalExceptionCallback;
    oCdbWrapper.fFinishedCallback = fFinishedCallback;
    oCdbWrapper.fPageHeapNotEnabledCallback = fPageHeapNotEnabledCallback;
    oCdbWrapper.fStdInInputCallback = fStdInInputCallback;
    oCdbWrapper.fStdOutOutputCallback = fStdOutOutputCallback;
    oCdbWrapper.fStdErrOutputCallback = fStdErrOutputCallback;
    oCdbWrapper.fNewProcessCallback = fNewProcessCallback;
    
    # Get the cdb binary path
    oCdbWrapper.sDebuggingToolsPath = dxConfig["sDebuggingToolsPath_%s" % oCdbWrapper.sCdbISA];
    assert oCdbWrapper.sDebuggingToolsPath, "No %s Debugging Tools for Windows path found" % oCdbWrapper.sCdbISA;
    oCdbWrapper.doProcess_by_uId = {};
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
    oCdbWrapper.oBugReport = None; # Set to a bug report if a bug was detected in the application
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
    oCdbWrapper.bCdbHasBeenAskedToInterruptApplication = False; # Will be set to true while the application is running and being interrupted in cdb.
    # Lock for the above four timeout and interrupt variables
    oCdbWrapper.oTimeoutAndInterruptLock = threading.RLock();
    oCdbWrapper.bCdbStdInOutThreadRunning = True; # Will be set to false if the thread terminates for any reason.
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
    asCommandLine = [
      os.path.join(oCdbWrapper.sDebuggingToolsPath, "cdb.exe"),
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
      asCommandLine += ["-y", sSymbolsPath];
    # Create a thread that interacts with the debugger to debug the application
    oCdbWrapper.oCdbStdInOutThread = oCdbWrapper.foVitalThread(cCdbWrapper_fCdbStdInOutThread);
    # Create a thread that reads stderr output and shows it in the console
    oCdbWrapper.oCdbStdErrThread = oCdbWrapper.foVitalThread(cCdbWrapper_fCdbStdErrThread);
    # Create a thread that waits for the debugger to terminate and cleans up after it.
    oCdbWrapper.oCdbCleanupThread = oCdbWrapper.foVitalThread(cCdbWrapper_fCdbCleanupThread);
    # We may need to start a dummy process if we're starting a UWP application. See below.
    if oCdbWrapper.sApplicationBinaryPath is not None:
      # If a process must be started, add it to the command line.
      assert not oCdbWrapper.auProcessIdsPendingAttach, \
          "Cannot start a process and attach to processes at the same time";
      asCommandLine += [oCdbWrapper.sApplicationBinaryPath] + oCdbWrapper.asApplicationArguments;
    elif oCdbWrapper.oUWPApplication:
      assert len(oCdbWrapper.asApplicationArguments) <= 1, \
          "You cannot specify multiple arguments for a UWP application.";
      # Unfortunately, we cannot start cdb without starting an application, so we're going to start a dummy
      # application that we can terminate once we've started and attached to the UWP application. This is going
      # to be a python script that simply waits for a number of seconds. If cdb.exe does not attach to the UWP
      # application before then, we'll report an error.
      asCommandLine += [
        sys.executable, "-c", "import time;time.sleep(%f)" % dxConfig["nUWPApplicationAttachTimeout"], 
      ];
    else:
      assert oCdbWrapper.auProcessIdsPendingAttach, \
          "Must start a process or attach to one";
      # If any processes must be attached to, add the first to the coommand line.
      asCommandLine += ["-p", str(oCdbWrapper.auProcessIdsPendingAttach[0])];
    # Quote any non-quoted argument that contain spaces:
    asCommandLine = [
      (x and (x[0] == '"' or x.find(" ") == -1)) and x or '"%s"' % x.replace('"', '\\"')
      for x in asCommandLine
    ];
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
  
  def foVitalThread(oCdbWrapper, fActivity):
    return threading.Thread(target = oCdbWrapper.__fThreadWrapper, args = (fActivity, True));
  
  def foHelperThread(oCdbWrapper, fActivity):
    return threading.Thread(target = oCdbWrapper.__fThreadWrapper, args = (fActivity, False));
  
  def __fThreadWrapper(oCdbWrapper, fActivity, bVital):
    try:
      try:
        fActivity(oCdbWrapper);
      except Exception, oException:
        oCdbWrapper.aoInternalExceptions.append(oException);
        cException, oException, oTraceBack = sys.exc_info();
        if oCdbWrapper.fInternalExceptionCallback:
          oCdbWrapper.fInternalExceptionCallback(oException, oTraceBack);
        else:
          raise;
    finally:
      oCdbProcess = getattr(oCdbWrapper, "oCdbProcess", None);
      if not oCdbProcess:
        oCdbWrapper.bCdbRunning = False;
        return;
      if oCdbProcess.poll() is not None:
        oCdbWrapper.bCdbRunning = False;
        return;
      if bVital:
        # A vital thread terminated and cdb is still running: terminate cdb
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
        fbTerminateProcessForId(oCdbProcess.pid);
        # Make sure cdb finally died.
        assert oCdbProcess.poll() is not None, \
            "cdb did not die after killing it repeatedly";
        oCdbWrapper.bCdbRunning = False;
  
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
  
  def fAskCdbToInterruptApplication(oCdbWrapper):
    cCdbWrapper_fAskCdbToInterruptApplication(oCdbWrapper);
  
  def fLogMessageInReport(oCdbWrapper, sMessageClass, sMessage):
    if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      oCdbWrapper.sLogHTML += "<span class=\"%s\">%s</span><br/>" % \
          (oCdbWrapper.fsHTMLEncode(sMessageClass), oCdbWrapper.fsHTMLEncode(sMessage));
