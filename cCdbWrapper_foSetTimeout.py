import time;
from .cTimeout import cTimeout;

def cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, nTimeoutInSeconds, fCallback, *axCallbackArguments):
  assert nTimeoutInSeconds >= 0, "Negative timeout time does not make sense";
  oCdbWrapper.oApplicationTimeLock.fAcquire();
  try:
    nFireAtOrAfterApplicationRunTimeInSeconds = nTimeoutInSeconds and oCdbWrapper.nApplicationRunTime + nTimeoutInSeconds;
    if oCdbWrapper.bApplicationIsRunning:
      # The application is currently running, make an estimate for how long to determine when to stop the application:
      nFireAtOrAfterApplicationRunTimeInSeconds += time.clock() - oCdbWrapper.nApplicationResumeTime;
  finally:
    oCdbWrapper.oApplicationTimeLock.fRelease();
  oTimeout = cTimeout(sDescription, nFireAtOrAfterApplicationRunTimeInSeconds, fCallback, axCallbackArguments);
  oCdbWrapper.aoTimeouts.append(oTimeout);
  return oTimeout;
