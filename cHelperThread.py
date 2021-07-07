import sys;

from .cCdbStoppedException import cCdbStoppedException;
from mMultiThreading import cLock, cThread;

class cHelperThread(object):
  def __init__(oSelf, oCdbWrapper, sName, fActivity, *axActivityArguments, **dxFlags):
    for sFlag in dxFlags:
      assert sFlag in ["bVital"], \
          "Unknown flag %s" % sFlag;
    oSelf.__oCdbWrapper = oCdbWrapper;
    oSelf.sName = sName;
    oSelf.__fActivity = fActivity
    oSelf.__axActivityArguments = axActivityArguments; 
    oSelf.__bVital = dxFlags.get("bVital", False); # Vital in this respect means kill cdb.exe if the thread terminates.
    
    oSelf.__oThread = None;
    oSelf.__oStartedLock = cLock(n0DeadlockTimeoutInSeconds = 1);
    
  def __str__(oSelf):
    uThreadId = oSelf.uId;
    sThreadId = ("#%d" % uThreadId) if uThreadId else "not started";
    return "Thread %s [%s] %s(%s)" % (sThreadId, oSelf.sName, repr(oSelf.__fActivity), ", ".join([repr(xArgument) for xArgument in oSelf.__axActivityArguments]));
  
  @property
  def bIsRunning(oSelf):
    # Consider it running between the moment it was started to the moment it terminated. This includes the brief moment
    # where the thread is started but not yet running.
    return (oSelf.__oThread.bStarted and not oSelf.__oThread.bTerminated) if oSelf.__oThread else False;
  
  @property
  def uId(oSelf):
    return oSelf.__oThread.uId if oSelf.__oThread else None;
  
  def fbIsCurrentThread(oSelf):
    return oSelf.__oThread == cThread.foGetCurrent();
  
  def fStart(oSelf):
    assert not oSelf.bIsRunning, \
        "Cannot run twice in parallel.";
    try:
      oSelf.__oThread = cThread(oSelf.__fRun);
    except thread.error as oException:
      # We cannot create another thread. The most obvious reason for this error is that there are too many threads
      # already. This might be caused by our threads not terminating as expected. To debug this, we will dump the
      # running threads, so we might detect any threads that should have terminated but haven't.
      print("Threads:");
      for oHelperThread in oSelf.__oCdbWrapper.aoActiveHelperThreads:
        print(" + %s" % oHelperThread);
    assert not oSelf.bIsRunning, \
        "Cannot start a thread while it is running";
    oSelf.__oCdbWrapper.aoActiveHelperThreads.append(oSelf);
    oSelf.__oStartedLock.fAcquire();
    oSelf.__oThread.fStart();
    oSelf.__oStartedLock.fWait();
  
  def fWait(oSelf):
    oSelf.__oThread.fWait();
  
  def __fRun(oSelf):
    oSelf.__oStartedLock.fRelease();
    oSelf.__oCdbWrapper.fbFireCallbacks("Log message", "helper thread started", {
      "Thread": str(oSelf),
    });
    try:
      try:
        oSelf.__fActivity(*oSelf.__axActivityArguments);
      except cCdbStoppedException as oCdbStoppedException:
        # There is only one type of exception that is expected which is raised in the cdb stdin/out thread when cdb has
        # terminated. This exception is only used to terminate that thread and should be caught and handled here, to
        # prevent it from being reported as an (unexpected) internal exception.
        pass;
      except Exception as oException:
        cException, oException, oTraceBack = sys.exc_info();
        if not oSelf.__oCdbWrapper.fbFireCallbacks("Internal exception", oSelf.__oThread, oException, oTraceBack):
          oSelf.__oCdbWrapper.fTerminate();
          raise;
    finally:
      oSelf.__oCdbWrapper.aoActiveHelperThreads.remove(oSelf);
      oSelf.__oCdbWrapper.fbFireCallbacks("Log message", "helper thread terminated", {
        "Thread": str(oSelf),
      });
      if oSelf.__bVital and oSelf.__oCdbWrapper.bCdbIsRunning:
        if oSelf.__oCdbWrapper.oCdbConsoleProcess and oSelf.__oCdbWrapper.oCdbConsoleProcess.bIsRunning:
          # A vital thread terminated and cdb is still running: terminate cdb
          oSelf.__oCdbWrapper.oCdbConsoleProcess.fbTerminate()
          assert not oSelf.__oCdbWrapper.oCdbConsoleProcess.bIsRunning, \
              "Could not terminate cdb";
        oSelf.__oCdbWrapper.bCdbIsRunning = False;
