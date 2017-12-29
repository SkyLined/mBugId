import time, threading;
from cBugReport_CdbCouldNotBeTerminated import cBugReport_CdbCouldNotBeTerminated;
from cBugReport_CdbTerminatedUnexpectedly import cBugReport_CdbTerminatedUnexpectedly;
from mWindowsAPI import *;

def fCleanup(oCdbWrapper):
  # Make sure the cdb.exe process is terminated:
  oCdbConsoleProcess = oCdbWrapper.oCdbConsoleProcess;
  if oCdbConsoleProcess:
    try:
      oCdbConsoleProcess.fbTerminate(5);
    except:
      oBugReport = cBugReport_CdbCouldNotBeTerminated(oCdbWrapper);
      oBugReport.fReport(oCdbWrapper);
    else:
      if not oCdbWrapper.bCdbWasTerminatedOnPurpose:
        oBugReport = cBugReport_CdbTerminatedUnexpectedly(oCdbWrapper, oCdbConsoleProcess.uExitCode);
        oBugReport.fReport(oCdbWrapper);
  
  # Make sure all processes for the application are terminated:
  auProcessIds = oCdbWrapper.doConsoleProcess_by_uId.keys() + oCdbWrapper.doProcess_by_uId.keys();
  for uProcessId in auProcessIds:
    fbTerminateProcessForId(uProcessId);
  # Wait for all other threads to terminate.
  # When a thread is started, information about it is added to a list. When the thread terminates, it's information is
  # removed from the list. This function runs in a separate thread as well. While there is more than one itme in the
  # list, we wait for the termination of each _other_ thread who's information is in the list. Once there is only one
  # thread left (the thread running this function), we are sure that BugId has come to a full stop.
  oCurrentThread = threading.currentThread();
  while len(oCdbWrapper.adxThreads) > 1:
    for dxThread in oCdbWrapper.adxThreads:
      oThread = dxThread["oThread"];
      if oThread != oCurrentThread:
        oThread.join();

def cCdbWrapper_fCleanupThread(oCdbWrapper):
  # wait for debugger thread to terminate.
  oCdbWrapper.oCdbStdInOutThread.join();
  # wait for stderr thread to terminate.
  oCdbWrapper.oCdbStdErrThread.join();
  try:
    # Cleanup is done in a try: ... finally: to make sure we fire the Finished event, or you could be waiting forever.
    fCleanup(oCdbWrapper);
  finally:
    oCdbWrapper.fbFireEvent("Log message", "Finished");
    oCdbWrapper.fbFireEvent("Finished");
    
