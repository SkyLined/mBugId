import threading;
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

from cCdbWrapper import cCdbWrapper;
from sVersion import sVersion;

class cBugId(object):
  sVersion = sVersion;
  # This is not much more than a wrapper for cCdbWrapper which only exposes those things that should be exposed:
  def __init__(oBugId,
    sCdbISA = None, # Which version of cdb should be used to debug this application?
    asApplicationCommandLine = None,
    auApplicationProcessIds = None,
    asLocalSymbolPaths = None,
    asSymbolCachePaths = None, 
    asSymbolServerURLs = None,
    dsURLTemplate_by_srSourceFilePath = None,
    rImportantStdOutLines = None,
    rImportantStdErrLines = None,
    bGenerateReportHTML = False,
    fApplicationRunningCallback = None,
    fExceptionDetectedCallback = None,
    fApplicationExitCallback = None,
    fFinishedCallback = None,
    fInternalExceptionCallback = None,
  ):
    # Replace fFinishedCallback with a wrapper that signals the finished event.
    # This event is used by the fWait function to wait for the process to
    # finish.
    oBugId.__fExternalFinishedCallback = fFinishedCallback;
    oBugId.__oFinishedEvent = threading.Event();
    oBugId.__bStarted = False;
    # Run the application in a debugger and catch exceptions.
    oBugId.__oCdbWrapper = cCdbWrapper(
      oBugId = oBugId,
      sCdbISA = sCdbISA,
      asApplicationCommandLine = asApplicationCommandLine,
      auApplicationProcessIds = auApplicationProcessIds,
      asLocalSymbolPaths = asLocalSymbolPaths,
      asSymbolCachePaths = asSymbolCachePaths,
      asSymbolServerURLs = asSymbolServerURLs,
      dsURLTemplate_by_srSourceFilePath = dsURLTemplate_by_srSourceFilePath,
      rImportantStdOutLines = rImportantStdOutLines,
      rImportantStdErrLines = rImportantStdErrLines,
      bGenerateReportHTML = bGenerateReportHTML,
      fApplicationRunningCallback = fApplicationRunningCallback,
      fExceptionDetectedCallback = fExceptionDetectedCallback,
      fApplicationExitCallback = fApplicationExitCallback,
      fFinishedCallback = oBugId.__fInternalFinishedHandler,
      fInternalExceptionCallback = fInternalExceptionCallback,
    );
  
  def fStart(oBugId):
    oBugId.__bStarted = True;
    oBugId.__oCdbWrapper.fStart();
  
  def fStop(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fStop()";
    oBugId.__oCdbWrapper.fStop();
  
  def fWait(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fWait()";
    while 1:
      try:
        oBugId.__oFinishedEvent.wait();
      except KeyboardInterrupt:
        continue;
      break;
  
  def fSetCheckForExcessiveCPUUsageTimeout(oBugId, nTimeout):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fSetCheckForExcessiveCPUUsageTimeout()";
    oBugId.__oCdbWrapper.fSetCheckForExcessiveCPUUsageTimeout(nTimeout);
  
  def fxSetTimeout(oBugId, nTimeout, fCallback, *axTimeoutCallbackArguments):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fxSetTimeout()";
    return oBugId.__oCdbWrapper.fxSetTimeout(nTimeout, fCallback, *axTimeoutCallbackArguments);
  
  def fClearTimeout(oBugId, xTimeout):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fClearTimeout()";
    oBugId.__oCdbWrapper.fClearTimeout(xTimeout);
  
  def fnApplicationRunTime(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fnApplicationRunTime()";
    return oBugId.__oCdbWrapper.fnApplicationRunTime();
  
  def fbFinished(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fbFinished()";
    oBugId.__oFinishedEvent.isSet();
  
  def __fInternalFinishedHandler(oBugId, oBugId2, oBugReport):
    oBugId.oBugReport = oBugReport;
    oBugId.__oFinishedEvent.set();
    oBugId.__fExternalFinishedCallback and oBugId.__fExternalFinishedCallback(oBugId, oBugReport);
