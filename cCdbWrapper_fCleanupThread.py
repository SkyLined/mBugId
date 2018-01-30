import time, threading;
from cBugReport_CdbCouldNotBeTerminated import cBugReport_CdbCouldNotBeTerminated;
from cBugReport_CdbTerminatedUnexpectedly import cBugReport_CdbTerminatedUnexpectedly;
from mWindowsAPI import *;


def cCdbWrapper_fCleanupThread(oCdbWrapper):
  # wait for debugger thread to terminate.
  oCdbWrapper.oCdbStdInOutThread.join();
  oCdbWrapper.fbFireEvent("Log message", "cdb stdin/out closed");
  if not oCdbWrapper.bCdbWasTerminatedOnPurpose:
    if not oCdbWrapper.oCdbConsoleProcess.bIsRunning:
      oBugReport = cBugReport_CdbTerminatedUnexpectedly(oCdbWrapper, oCdbConsoleProcess.uExitCode);
      oBugReport.fReport(oCdbWrapper);
    elif not oCdbWrapper.oCdbConsoleProcess.fbTerminate(5):
      oBugReport = cBugReport_CdbCouldNotBeTerminated(oCdbWrapper);
      oBugReport.fReport(oCdbWrapper);
    else:
      oCdbWrapper.fbFireEvent("Log message", "cdb.exe terminated");
  # wait for stderr thread to terminate.
  oCdbWrapper.oCdbStdErrThread.join();
  oCdbWrapper.fbFireEvent("Log message", "cdb stderr closed");
  if oCdbWrapper.bCdbWasTerminatedOnPurpose:
    # Wait for cdb.exe to terminate
    oCdbWrapper.oCdbConsoleProcess.fbWait();
    oCdbWrapper.fbFireEvent("Log message", "cdb.exe terminated");
  # Wait for all other threads to terminate
  oCurrentThread = threading.currentThread();
  while len(oCdbWrapper.adxThreads) > 1:
    for dxThread in oCdbWrapper.adxThreads:
      oThread = dxThread["oThread"];
      if oThread != oCurrentThread:
        # There is no timeout on this join, so we may hang forever. To be able to analyze such a bug, we will log the
        # details of the thread we are waiting on here:
        oCdbWrapper.fbFireEvent("Log message", "Waiting for thread %d %s(%s)" % \
            (oThread.ident, repr(dxThread["fActivity"]), ", ".join([repr(xArgument) for xArgument in dxThread["axActivityArguments"]])));
        oThread.join();
  # Report that we're finished.
  oCdbWrapper.fbFireEvent("Log message", "Finished");
  oCdbWrapper.fbFireEvent("Finished");
    
