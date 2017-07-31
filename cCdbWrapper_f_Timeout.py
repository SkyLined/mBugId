import time;
from cTimeout import cTimeout;

def cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, nTimeToWait, fCallback, *axCallbackArguments):
  assert nTimeToWait >= 0, "Negative timeout time does not make sense";
  oCdbWrapper.oTimeoutAndInterruptLock.acquire();
  try:
    oCdbWrapper.oApplicationTimeLock.acquire();
    try:
      nFireAtOrAfterApplicationRunTime = oCdbWrapper.nApplicationRunTime + nTimeToWait;
      if oCdbWrapper.bApplicationIsRunnning:
        # The application is currently running, make an estimate for how long to determine when to stop the application:
        nFireAtOrAfterApplicationRunTime += time.clock() - oCdbWrapper.nApplicationResumeTime;
    finally:
      oCdbWrapper.oApplicationTimeLock.release();
    oTimeout = cTimeout(sDescription, nFireAtOrAfterApplicationRunTime, fCallback, axCallbackArguments);
    oCdbWrapper.aoTimeouts.append(oTimeout);
    if nTimeToWait == 0 and oCdbWrapper.bApplicationIsRunnning and not oCdbWrapper.bCdbHasBeenAskedToInterruptApplication:
      # This timeout should fire immediately, but the application is running and cdb has not been interrupted
      oCdbWrapper.fAskCdbToInterruptApplication();
  finally:
    oCdbWrapper.oTimeoutAndInterruptLock.release();
  return oTimeout;

def cCdbWrapper_fClearTimeout(oCdbWrapper, oTimeout):
  oCdbWrapper.oTimeoutAndInterruptLock.acquire();
  try:
    if oTimeout in oCdbWrapper.aoFutureTimeouts:
      oCdbWrapper.aoTimeouts.remove(oTimeout);
  finally:
    oCdbWrapper.oTimeoutAndInterruptLock.release();