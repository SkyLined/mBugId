import time;
from .dxConfig import dxConfig;

def cCdbWrapper_fCdbInterruptOnTimeoutHelperThread(oCdbWrapper):
  # Thread that is started when the application is started or resumed and which should terminate when it is paused.
  while oCdbWrapper.bApplicationIsRunning:
    # It checks if a timeout has fired every N seconds (N = nTimeoutGranularityInSeconds in dxConfig.py).
    time.sleep(dxConfig["nTimeoutGranularityInSeconds"]);
    for oTimeout in oCdbWrapper.aoTimeouts[:]:
      if oTimeout.fbShouldFire(oCdbWrapper.nApplicationRunTimeInSeconds):
        # Yes, interrupt the application so the timeouts can be fired and then stop looking through the list.
        oCdbWrapper.fbFireCallbacks("Log message", "Interrupting application to fire timeout", {
          "Timeout": oTimeout.sDescription
        });
        oCdbWrapper.fInterruptApplicationExecution();
        return; # The application will be interrupted, so this thread should stop.
