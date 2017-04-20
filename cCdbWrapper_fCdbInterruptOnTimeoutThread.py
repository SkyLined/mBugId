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
      for (nTimeoutApplicationRunTime, fTimeoutCallback, axTimeoutCallbackArguments) in oCdbWrapper.axTimeouts: # Make a copy so modifcation during the loop does not affect it.
        if nTimeoutApplicationRunTime <= nApplicationRunTime:
          # Let the StdIO thread know a break exception was sent so it knows to expected cdb to report one (otherwise
          # it would get reported as a bug!).
          oCdbWrapper.uCdbBreakExceptionsPending += 1;
          for x in xrange(9): # Try up to 10 times, the first 9 times an error will cause a retry.
            try:
              oCdbWrapper.oCdbProcess.send_signal(signal.CTRL_BREAK_EVENT);
            except:
              if not oCdbWrapper.bCdbRunning: return;
              time.sleep(0.1); # Sleep a bit, maybe the problem will go away?
              continue;
            break;
          else:
            oCdbWrapper.oCdbProcess.send_signal(signal.CTRL_BREAK_EVENT); # 10th time time; don't handle errors
          break;
      oCdbWrapper.oTimeoutsLock.release();
    finally:
      oCdbWrapper.oCdbLock.release();
    time.sleep(dxConfig["nTimeoutGranularity"]);
