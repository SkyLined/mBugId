import time;
from .dxConfig import dxConfig;

def cCdbWrapper_fCdbInterruptOnTimeoutHelperThread(oCdbWrapper):
  # Thread that checks if a timeout has fired every N seconds (N = nTimeoutInterruptGranularity in dxConfig.py).
  while 1:
    oCdbWrapper.oTimeoutAndInterruptLock.acquire();
    try:
      if any([
        # If the application is no longer running...
        not oCdbWrapper.bApplicationIsRunnning,
        # ...or cdb.exe if no longer running...
        not oCdbWrapper.bCdbRunning,
        # ...or the application is about to be interrupted already...
        oCdbWrapper.uUtilityInterruptThreadId is not None,
      ]):
        # .... then this thread is no longer needed.
        return; 
      # Otherwise, check if any timeout should be fired:
      for oTimeout in oCdbWrapper.aoTimeouts[:]:
        if oTimeout.fbShouldFire(oCdbWrapper.nApplicationRunTime):
          oCdbWrapper.fbFireEvent("Log message", "Interrupting application to fire timeout", {
            "Timeout": oTimeout.sDescription
          });
          oCdbWrapper.fInterruptApplicationExecution();
          return;
    finally:
      oCdbWrapper.oTimeoutAndInterruptLock.release();
    # Wait for a bit before checking again
    time.sleep(dxConfig["nTimeoutGranularity"]);
