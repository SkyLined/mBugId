import signal, time;

from dxBugIdConfig import dxBugIdConfig;

bDebugOutput = False;

def cCdbWrapper_fCdbInterruptOnTimeoutThread(oCdbWrapper):
  # Thread that checks if a timeout has fired every N seconds (N = nTimeoutInterruptGranularity in dxBugIdConfig).
  while 1:
    if bDebugOutput:
      print "@@@ waiting for application to run...";
    bTimeout = False;
    # Wait for cdb to be running or have terminated...
    oCdbWrapper.oCdbLock.acquire();
    try:
      # Stop as soon as debugging has stopped.
      if not oCdbWrapper.bCdbRunning: return;
      if not oCdbWrapper.bCdbStdInOutThreadRunning: return;
      # Time spent running before the application was resumed + time since the application was resumed.
      nApplicationRunTime = oCdbWrapper.fnApplicationRunTime();
      if bDebugOutput:
        print "@@@ application run time    : %.3f" % nApplicationRunTime;
        print "@@@ number of timeouts      : %d" % len(oCdbWrapper.axTimeouts);
      oCdbWrapper.oTimeoutsLock.acquire();
      for (nTimeoutTime, fTimeoutCallback, axTimeoutCallbackArguments) in oCdbWrapper.axTimeouts: # Make a copy so modifcation during the loop does not affect it.
        if nTimeoutTime <= nApplicationRunTime:
          # Let the StdIO thread know a break exception was sent so it knows to expected cdb to report one (otherwise
          # it would get reported as a bug!).
          oCdbWrapper.uCdbBreakExceptionsPending += 1;
          for x in xrange(4): # Try up to 5 times, handle errors the first 4 times.
            try:
              oCdbWrapper.oCdbProcess.send_signal(signal.CTRL_BREAK_EVENT);
            except:
              if not oCdbWrapper.bCdbRunning: return;
              continue;
            break;
          else:
            oCdbWrapper.oCdbProcess.send_signal(signal.CTRL_BREAK_EVENT); # 5th time; don't handle errors
          if bDebugOutput:
            print "@@@ timeout for %.3f/%.3f => %s" % (nTimeoutTime - nApplicationRunTime, nTimeoutTime, repr(fTimeoutCallback));
          break;
        elif bDebugOutput:
          print "@@@ sleep for %.3f/%.3f => %s" % (nTimeoutTime - nApplicationRunTime, nTimeoutTime, repr(fTimeoutCallback));
      oCdbWrapper.oTimeoutsLock.release();
    finally:
      oCdbWrapper.oCdbLock.release();
    if bDebugOutput:
      print "@@@ sleeping until next possible timeout...";
    time.sleep(dxBugIdConfig["nTimeoutGranularity"]);
