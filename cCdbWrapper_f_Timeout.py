import time;
from cTimeout import cTimeout;

def cCdbWrapper_foSetTimeout(oCdbWrapper, nTime, fCallback, *axCallbackArguments):
  assert nTime >= 0, "Negative timeout time does not make sense";
  oCdbWrapper.oApplicationTimeLock.acquire();
  try:
    nTimeoutApplicationRunTime = oCdbWrapper.nApplicationRunTime + nTime;
    if oCdbWrapper.nApplicationResumeTime:
      # The application is currently running, make an estimate for how long to determine when to stop the application:
      nTimeoutApplicationRunTime += time.clock() - oCdbWrapper.nApplicationResumeTime;
  finally:
    oCdbWrapper.oApplicationTimeLock.release();
  oTimeout = cTimeout(nTimeoutApplicationRunTime, fCallback, axCallbackArguments);
  oCdbWrapper.oTimeoutsLock.acquire();
  try:
    # If would be nice to be able to interrupt an application immediately, but when I tried this in the stderr
    # handling thread, the CTRL+BREAK terminated cdb immediately, rather than interrupt the application. So, we will
    # queue the timeout, even if it should fire immediately and hope the interrupt-on-timeout thread will fire it soon.

#    if nTime > 0:
      # Queue this timeout
      oCdbWrapper.aoFutureTimeouts.append(oTimeout);
#    else:
#      # Fire this timeout immediately
#      oCdbWrapper.aoCurrentTimeouts.append(oTimeout);
#      oCdbWrapper.fMakeSureApplicationIsInterruptedToHandleTimeouts();
  finally:
    oCdbWrapper.oTimeoutsLock.release();
  return oTimeout;

def cCdbWrapper_fClearTimeout(oCdbWrapper, oTimeout):
  oCdbWrapper.oTimeoutsLock.acquire();
  try:
    if oTimeout in oCdbWrapper.aoFutureTimeouts:
      oCdbWrapper.aoFutureTimeouts.remove(oTimeout);
    if oTimeout in oCdbWrapper.aoCurrentTimeouts:
      oCdbWrapper.aoCurrentTimeouts.remove(oTimeout);
  finally:
    oCdbWrapper.oTimeoutsLock.release();