import signal, time;
from dxConfig import dxConfig;

def cCdbWrapper_fCdbInterruptOnTimeoutThread(oCdbWrapper):
  # Thread that checks if a timeout has fired every N seconds (N = nTimeoutInterruptGranularity in dxConfig.py).
  while 1:
    bTimeout = False;
    # Wait for cdb to be running or have terminated...
    oCdbWrapper.oCdbLock.acquire();
    try:
      # Stop as soon as debugging has stopped.
      if not oCdbWrapper.bCdbRunning: return;
      if not oCdbWrapper.bCdbStdInOutThreadRunning: return;
      # Time spent running before the application was resumed + time since the application was resumed.
      nApplicationRunTime = oCdbWrapper.fnApplicationRunTime();
      oCdbWrapper.oTimeoutsLock.acquire();
      try:
        for oTimeout in oCdbWrapper.aoTimeouts:
          if oTimeout.fbShouldFire(nApplicationRunTime):
            oCdbWrapper.fMakeSureApplicationIsInterruptedToHandleTimeouts();
            break;
      finally:
        oCdbWrapper.oTimeoutsLock.release();
    finally:
      oCdbWrapper.oCdbLock.release();
    time.sleep(dxConfig["nTimeoutGranularity"]);
