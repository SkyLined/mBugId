import sys, threading;

from cCdbStoppedException import cCdbStoppedException;

class cHelperThread(object):
  def __init__(oSelf, oCdbWrapper, sName, fActivity, *axActivityArguments, **dxFlags):
    for sFlag in dxFlags:
      assert sFlag in ["bVital"], \
          "Unknown flag %s" % sFlag;
    oSelf.__oCdbWrapper = oCdbWrapper;
    oSelf.sName = sName;
    oSelf.__fActivity = fActivity
    oSelf.__axActivityArguments = axActivityArguments; 
    oSelf.__bVital = dxFlags.get("bVital", False);
    
    oSelf.__oThread = None
    oSelf.__oWaitLock = threading.Lock();
    
  def __str__(oSelf):
    sId = "#%d" % oSelf.__oThread.ident if oSelf.__oThread else "not started";
    return "Thread %s [%s] %s(%s)" % (sId, oSelf.sName, repr(oSelf.__fActivity), ", ".join([repr(xArgument) for xArgument in oSelf.__axActivityArguments]));
  
  @property
  def bRunning(oSelf):
    return oSelf in oSelf.__oCdbWrapper.aoActiveHelperThreads;
  
  @property
  def uId(oSelf):
    return oSelf.__oThread and oSelf.__oThread.ident;
  
  def fbIsCurrentThread(oSelf):
    return threading.currentThread().ident == oSelf.uId;
  
  def fStart(oSelf):
    try:
      oSelf.__oThread = threading.Thread(target = oSelf.__fRun);
    except thread.error as oException:
      # We cannot create another thread. The most obvious reason for this error is that there are too many threads
      # already. This might be cause by our threads not terminating as expected. To debug this, we will dump the
      # running threads, so we might detect any threads that should have terminated but haven't.
      print "Threads:";
      for oHelperThread in oSelf.__oCdbWrapper.aoActiveHelperThreads:
        print " + %s" % oHelperThread;
    assert not oSelf.bRunning, \
        "Cannot start a thread while it is running";
    oSelf.__oCdbWrapper.aoActiveHelperThreads.append(oSelf);
    oSelf.__oWaitLock.acquire();
    oSelf.__oThread.start();
  
  def fWait(oSelf):
    oSelf.__oWaitLock.acquire();
    oSelf.__oWaitLock.release();
  
  def __fRun(oSelf):
    oSelf.__oCdbWrapper.fbFireEvent("Log message", "helper thread started", {
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
      except Exception, oException:
        cException, oException, oTraceBack = sys.exc_info();
        if not oSelf.__oCdbWrapper.fbFireEvent("Internal exception", oException, oTraceBack):
          oSelf.__oCdbWrapper.fTerminate();
          raise;
    finally:
      oSelf.__oCdbWrapper.aoActiveHelperThreads.remove(oSelf);
      oSelf.__oWaitLock.release();
      oSelf.__oCdbWrapper.fbFireEvent("Log message", "helper thread terminated", {
        "Thread": str(oSelf),
      });
      if oSelf.__bVital and oSelf.__oCdbWrapper.bCdbRunning:
        if oSelf.__oCdbWrapper.oCdbConsoleProcess and oSelf.__oCdbWrapper.oCdbConsoleProcess.bIsRunning:
          # A vital thread terminated and cdb is still running: terminate cdb
          oSelf.__oCdbWrapper.oCdbConsoleProcess.fbTerminate()
          assert not oSelf.__oCdbWrapper.oCdbConsoleProcess.bIsRunning, \
              "Could not terminate cdb";
        oSelf.__oCdbWrapper.bCdbRunning = False;
