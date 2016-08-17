import threading;
from cCdbWrapper import cCdbWrapper;
from sVersion import sVersion;

for (sModule, sURL) in {
  "FileSystem": "https://github.com/SkyLined/FileSystem/",
  "Kill": "https://github.com/SkyLined/Kill/",
}.items():
  try:
    __import__(sModule, globals(), locals(), [], -1);
  except ImportError:
    print "*" * 80;
    print "BugId depends on %s, which you can download at:" % sModule;
    print "    %s" % sURL;
    print "After downloading, please save the code in the folder \"%s\"," % sModule;
    print "\"modules\\%s\" or any other location where it can be imported." % sModule;
    print "Once you have completed these steps, please try again.";
    print "*" * 80;
    raise;

class cBugId(object):
  sVersion = sVersion;
  def __init__(oBugId, **dxArguments):
    # Replace fFinishedCallback with a wrapper that signals the finished event.
    # This event is used by the fWait function to wait for the process to
    # finish.
    oBugId.__fExternalFinishedCallback = dxArguments.get("fFinishedCallback");
    dxArguments["fFinishedCallback"] = oBugId.__fInternalFinishedHandler;
    oBugId.__oFinishedEvent = threading.Event();
    # Run the application in a debugger and catch exceptions.
    oBugId.__oCdbWrapper = cCdbWrapper(**dxArguments);
  
  def fStop(oBugId):
    oBugId.__oCdbWrapper.fStop();
  
  def fWait(oBugId):
    while 1:
      try:
        oBugId.__oFinishedEvent.wait();
      except KeyboardInterrupt:
        continue;
      break;
  
  def fSetCheckForExcessiveCPUUsageTimeout(oBugId, nTimeout):
    oBugId.__oCdbWrapper.fSetCheckForExcessiveCPUUsageTimeout(nTimeout);
  
  def fxSetTimeout(oBugId, nTimeout, fCallback, *axArguments):
    return oBugId.__oCdbWrapper.fxSetTimeout(nTimeout, fCallback, *axArguments);
  
  def fClearTimeout(oBugId, xTimeout):
    oBugId.__oCdbWrapper.fClearTimeout(xTimeout);
  
  def fnApplicationRunTime(oBugId):
    return oBugId.__oCdbWrapper.fnApplicationRunTime();
  
  def fbFinished(oBugId):
    oBugId.__oFinishedEvent.isSet();
  
  def __fInternalFinishedHandler(oBugId, oBugReport):
    oBugId.oBugReport = oBugReport;
    oBugId.__oFinishedEvent.set();
    oBugId.__fExternalFinishedCallback and oBugId.__fExternalFinishedCallback(oBugReport);
