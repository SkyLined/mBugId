import time, threading;

from mWindowsAPI import *;
from mWindowsSDK import *;

from .cBugReport_CdbCouldNotBeTerminated import cBugReport_CdbCouldNotBeTerminated;
from .cBugReport_CdbTerminatedUnexpectedly import cBugReport_CdbTerminatedUnexpectedly;

def cCdbWrapper_fCleanupHelperThread(oCdbWrapper):
  # wait for debugger thread to terminate.
  oCdbWrapper.oCdbStdInOutHelperThread.fWait();
  oCdbWrapper.fbFireCallbacks("Log message", "cdb stdin/out closed");
  if not oCdbWrapper.bCdbWasTerminatedOnPurpose:
    if oCdbWrapper.oCdbConsoleProcess.bIsRunning and not oCdbWrapper.oCdbConsoleProcess.fbTerminate(5):
      oBugReport = cBugReport_CdbCouldNotBeTerminated(oCdbWrapper);
      oBugReport.fReport();
    elif oCdbWrapper.oCdbConsoleProcess.uExitCode & 0xCFFFFFFF != STATUS_PROCESS_IS_TERMINATING:
      oCdbWrapper.fbFireCallbacks("Log message", "cdb.exe terminated unexpectedly");
      oBugReport = cBugReport_CdbTerminatedUnexpectedly(oCdbWrapper, oCdbWrapper.oCdbConsoleProcess.uExitCode);
      oBugReport.fReport();
    else:
      oCdbWrapper.fbFireCallbacks("Log message", "The process terminated before the debugger could attach.");
  if oCdbWrapper.oUtilityProcess and oCdbWrapper.oUtilityProcess.bIsRunning:
    oCdbWrapper.fbFireCallbacks("Log message", "Terminating utility process...");
    if oCdbWrapper.oUtilityProcess.fbTerminate():
      oCdbWrapper.fbFireCallbacks("Log message", "Utility process termimated.");
  # wait for stderr thread to terminate.
  oCdbWrapper.oCdbStdErrHelperThread.fWait();
  oCdbWrapper.fbFireCallbacks("Log message", "cdb stderr closed");
  if oCdbWrapper.bCdbWasTerminatedOnPurpose:
    # Wait for cdb.exe to terminate
    oCdbWrapper.oCdbConsoleProcess.fbWait();
    oCdbWrapper.fbFireCallbacks("Log message", "cdb.exe terminated");
  
  # Make sure all application processes we started are terminated:
  for oApplicationProcess in oCdbWrapper.aoApplicationProcesses:
    oCdbWrapper.fbFireCallbacks("Log message", "Terminating application process %s..." % oApplicationProcess);
    try:
      oApplicationProcess.fTerminate();
    except Exception as oException:
      oCdbWrapper.fbFireCallbacks("Log message", "Application process %s could not be terminated: %s" % (oApplicationProcess, oException));
    else:
      oCdbWrapper.fbFireCallbacks("Log message", "Application process %s terminated." % oApplicationProcess);
  
  # Make sure all application processes' pipes are closed:
  for oPipe in oCdbWrapper.aoApplicationStdOutAndStdErrPipes:
    oCdbWrapper.fbFireCallbacks("Log message", "Closing application pipe %s..." % oPipe);
    try:
      oPipe.fClose();
    except Exception as oException:
      oCdbWrapper.fbFireCallbacks("Log message", "Application pipe %s could not be closed: %s" % (oPipe, oException));
    else:
      oCdbWrapper.fbFireCallbacks("Log message", "Application pipe %s closed." % oPipe);
  
  # Wait for all other threads to terminate
  while len(oCdbWrapper.aoActiveHelperThreads) > 1:
    for oHelperThread in oCdbWrapper.aoActiveHelperThreads:
      if oHelperThread == oCdbWrapper.oCleanupHelperThread: continue;
      # There is no timeout on this join, so we may hang forever. To be able to analyze such a bug, we will log the
      # details of the thread we are waiting on here:
      oCdbWrapper.fbFireCallbacks("Log message", "Waiting for thread", {
        "Thread": str(oHelperThread),
      });
      oHelperThread.fWait();
      # The list may have been changed while we waited, so start again.
      break;
  assert (
    len(oCdbWrapper.aoActiveHelperThreads) == 1 \
    and oCdbWrapper.aoActiveHelperThreads[0] == oCdbWrapper.oCleanupHelperThread
  ), \
      "Expected only cleanup helper thread to remain, got %s" % \
      ", ".join([str(oHelperThread) for oHelperThread in oCdbWrapper.aoActiveHelperThreads]);
  # Report that we're finished.
  oCdbWrapper.fbFireCallbacks("Log message", "Finished");
  oCdbWrapper.fbFireCallbacks("Finished");
    
