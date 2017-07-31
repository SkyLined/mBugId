import time;
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
      # Get exclusive access to timeout info
      oCdbWrapper.oTimeoutsLock.acquire();
      try:
        # If timeouts are already scheduled to fire, no need to schedule more here.
        if oCdbWrapper.aoCurrentTimeouts:
          return;
        # Time spent running before the application was resumed + time since the application was resumed.
        nApplicationRunTime = oCdbWrapper.fnApplicationRunTime();
        # Mark all future timeouts that should fire as current
        for oTimeout in oCdbWrapper.aoFutureTimeouts[:]:
          if oTimeout.fbShouldFire(nApplicationRunTime):
            oCdbWrapper.aoFutureTimeouts.remove(oTimeout);
            oCdbWrapper.aoCurrentTimeouts.append(oTimeout);
        # If any timeouts were marked as current, make sure the application is interrupted to handle them
        if oCdbWrapper.aoCurrentTimeouts:
          oCdbWrapper.fMakeSureApplicationIsInterruptedToHandleTimeouts();
      finally:
        oCdbWrapper.oTimeoutsLock.release();
    finally:
      oCdbWrapper.oCdbLock.release();
    time.sleep(dxConfig["nTimeoutGranularity"]);
