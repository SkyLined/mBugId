import time, threading;
from cBugReport_CdbTerminatedUnexpectedly import cBugReport_CdbTerminatedUnexpectedly;
from mWindowsAPI import *;

def cCdbWrapper_fCdbCleanupThread(oCdbWrapper):
  # wait for debugger thread to terminate.
  oCdbWrapper.oCdbStdInOutThread.join();
  # wait for stderr thread to terminate.
  oCdbWrapper.oCdbStdErrThread.join();
  # Terminate the cdb process in case it somehow is still running.
  try:
    oCdbWrapper.oCdbProcess.terminate();
  except:
    pass; # Apparently it wasn't running.
  # Make sure all stdio pipes are closed.
  try:
    oCdbWrapper.oCdbProcess.stdout.close();
  except:
    pass; # Apparently it wasn't open.
  try:
    oCdbWrapper.oCdbProcess.stderr.close();
  except:
    pass; # Apparently it wasn't open.
  try:
    oCdbWrapper.oCdbProcess.stdin.close();
  except:
    pass; # Apparently it wasn't open.
  # Wait for the cdb process to terminate
  uExitCode = oCdbWrapper.oCdbProcess.wait();
  # Destroy the subprocess object to make even more sure all stdio pipes are closed.
  del oCdbWrapper.oCdbProcess;
  # Determine if the debugger was terminated or if the application terminated. If not, an exception is thrown later, as
  # the debugger was not expected to stop, which is an unexpected error.
  bTerminationWasExpected = oCdbWrapper.bCdbWasTerminatedOnPurpose or len(oCdbWrapper.doProcess_by_uId) == 0;
  # There have also been cases where processes associated with an application were still running after this point in
  # the code. I have been unable to determine how this could happen but in an attempt to fix this, all process ids that
  # should be terminated are killed until they are confirmed they have terminated:
  uNumberOfTries = 10;
  while oCdbWrapper.doProcess_by_uId:
    auRunningProcessIds = fdsProcessesExecutableName_by_uId().keys();
    for (uProcessId, oProcess) in oCdbWrapper.doProcess_by_uId.items():
      if uProcessId not in auRunningProcessIds or fbTerminateProcessForId(uProcessId):
        del oCdbWrapper.doProcess_by_uId[uProcessId];
    if oCdbWrapper.doProcess_by_uId:
      uNumberOfTries -= 1;
      assert uNumberOfTries, \
          "Cannot terminate all processes";
      time.sleep(0.1);
  # Wait for all other threads to terminate.
  oCurrentThread = threading.currentThread();
#  print "Waiting for threads...";
  # When a thread is started, information about it is added to a list. When the thread terminates, it's information is
  # removed from the list. This function runs in a separate thread as well. While there is more than one itme in the
  # list, we wait for the termination of each _other_ thread who's information is in the list. Once there is only one
  # thread left (the thread running this function), we are sure that BugId has come to a full stop.
  while len(oCdbWrapper.adxThreads) > 1:
    for dxThread in oCdbWrapper.adxThreads:
      oThread = dxThread["oThread"];
      if oThread != oCurrentThread:
#        print "%04d %s(%s)" % (dxThread["oThread"].ident, repr(dxThread["fActivity"]), ", ".join([repr(xArgument) for xArgument in dxThread["axActivityArguments"]]));
        oThread.join();
  # Report this if it was not expected.
  if not bTerminationWasExpected:
    oCdbWrapper.oBugReport = cBugReport_CdbTerminatedUnexpectedly(oCdbWrapper, uExitCode);
  if oCdbWrapper.fFinishedCallback:
    oCdbWrapper.fFinishedCallback(oCdbWrapper.oBugReport);


