import time;
from dxConfig import dxConfig;

def cCdbWrapper_fCdbInterruptOnTimeoutThread(oCdbWrapper):
  # Thread that checks if a timeout has fired every N seconds (N = nTimeoutInterruptGranularity in dxConfig.py).
  while 1:
    oCdbWrapper.oTimeoutAndInterruptLock.acquire();
    try:
      if not oCdbWrapper.bApplicationIsRunnning or not oCdbWrapper.bCdbRunning or oCdbWrapper.bCdbHasBeenAskedToInterruptApplication:
        return; # This thread is no longer needed.
      # See if any timeout should be fired:
      for oTimeout in oCdbWrapper.aoTimeouts[:]:
        if oTimeout.fbShouldFire(oCdbWrapper.nApplicationRunTime):
          oCdbWrapper.fAskCdbToInterruptApplication();
          return;
    finally:
      oCdbWrapper.oTimeoutAndInterruptLock.release();
    # Wait for a bit before checking again
    time.sleep(dxConfig["nTimeoutGranularity"]);
