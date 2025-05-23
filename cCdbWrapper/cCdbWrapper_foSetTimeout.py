import time;
from ..cTimeout import cTimeout;

def cCdbWrapper_foSetTimeout(oCdbWrapper, sDescription, nTimeoutInSeconds, f0Callback = None, txCallbackArguments = []):
  assert nTimeoutInSeconds >= 0, "Negative timeout time does not make sense";
  oCdbWrapper.oApplicationTimeLock.fAcquire();
  try:
    nFireAtOrAfterApplicationRunTimeInSeconds = nTimeoutInSeconds and oCdbWrapper.nApplicationRunTimeInSeconds + nTimeoutInSeconds;
    if oCdbWrapper.bApplicationIsRunning:
      # The application is currently running, make an estimate for how long to determine when to stop the application:
      nFireAtOrAfterApplicationRunTimeInSeconds += time.time() - oCdbWrapper.n0ApplicationResumeTimeInSeconds;
  finally:
    oCdbWrapper.oApplicationTimeLock.fRelease();
  oTimeout = cTimeout(sDescription, nFireAtOrAfterApplicationRunTimeInSeconds, f0Callback, txCallbackArguments);
  oCdbWrapper.aoTimeouts.append(oTimeout);
  return oTimeout;
