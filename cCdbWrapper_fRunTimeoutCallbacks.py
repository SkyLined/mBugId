def cCdbWrapper_fRunTimeoutCallbacks(oCdbWrapper):
  ### Run timeout callbacks ######################################################################################
  # Execute any pending timeout callbacks (this can happen when the interrupt on timeout thread has interrupted
  # the application or whenever the application is paused for another exception - the interrupt on timeout thread
  # is just there to make sure the application gets interrupted to do so when needed: otherwise the timeout may not
  # fire until an exception happens by chance).
  while 1:
    # Timeouts can create new timeouts, which may need to fire immediately, so this is run in a loop until no more
    # timeouts need to be fired.
    aoTimeoutsToFire = [];
    for oTimeout in oCdbWrapper.aoTimeouts[:]:
      if oTimeout.fbShouldFire(oCdbWrapper.nApplicationRunTime):
        oCdbWrapper.aoTimeouts.remove(oTimeout);
        aoTimeoutsToFire.append(oTimeout);
    if not aoTimeoutsToFire:
      return;
    for oTimeoutToFire in aoTimeoutsToFire:
      oTimeoutToFire.fFire();
