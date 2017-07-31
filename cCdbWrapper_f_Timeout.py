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
    oCdbWrapper.aoTimeouts.append(oTimeout);
  finally:
    oCdbWrapper.oTimeoutsLock.release();
  return oTimeout;

def cCdbWrapper_fClearTimeout(oCdbWrapper, oTimeout):
  oCdbWrapper.oTimeoutsLock.acquire();
  try:
    if oTimeout in oCdbWrapper.aoTimeouts:
      oCdbWrapper.aoFutureTimeouts.remove(oTimeout);
  finally:
    oCdbWrapper.oTimeoutsLock.release();