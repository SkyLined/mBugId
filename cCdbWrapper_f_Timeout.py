import time;

def cCdbWrapper_fxSetTimeout(oCdbWrapper, nTime, fCallback, *axCallbackArguments):
#  print "@@@ timeout in %.1f seconds: %s" % (nTime, repr(fCallback));
  assert nTime >= 0, "Negative timeout time does not make sense";
  oCdbWrapper.oApplicationTimeLock.acquire();
  try:
    nTimeoutApplicationRunTime = oCdbWrapper.nApplicationRunTime + nTime;
    if oCdbWrapper.nApplicationResumeTime:
      # The application is currently running, make an estimate for how long to determine when to stop the application:
      nTimeoutApplicationRunTime += time.clock() - oCdbWrapper.nApplicationResumeTime;
  finally:
    oCdbWrapper.oApplicationTimeLock.release();
  xTimeout = (nTimeoutApplicationRunTime, fCallback, axCallbackArguments);
  oCdbWrapper.oTimeoutsLock.acquire();
  try:
    oCdbWrapper.axTimeouts.append(xTimeout);
#    print "@@@ number of timeouts: %d" % len(oCdbWrapper.axTimeouts);
  finally:
    oCdbWrapper.oTimeoutsLock.release();
  return xTimeout;

def cCdbWrapper_fClearTimeout(oCdbWrapper, xTimeout):
  (nTimeoutApplicationRunTime, fCallback, axCallbackArguments) = xTimeout;
  oCdbWrapper.oTimeoutsLock.acquire();
  try:
    if xTimeout in oCdbWrapper.axTimeouts:
      oCdbWrapper.axTimeouts.remove(xTimeout);
#      print "@@@ cleared timeout: %s" % repr(fCallback);
#    else:
#      # Timeout has already fired and been removed.
#      print "@@@ ignored clear fired timeout: %s" % repr(fCallback);
#    print "@@@ number of timeouts: %d" % len(oCdbWrapper.axTimeouts);
  finally:
    oCdbWrapper.oTimeoutsLock.release();