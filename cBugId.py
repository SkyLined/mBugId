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
from sOSISA import sOSISA;

class cBugId(object):
  sVersion = sVersion;
  sOSISA = sOSISA;
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
    fFailedToDebugApplicationCallback = None,
    fApplicationRunningCallback = None,
    fApplicationSuspendedCallback = None,
    fApplicationResumedCallback = None,
    fMainProcessTerminatedCallback = None,
    fInternalExceptionCallback = None,
    fFinishedCallback = None,
  ):
    # Replace fFinishedCallback with a wrapper that signals the finished event.
    # This event is used by the fWait function to wait for the process to
    # finish.
    oBugId.__fFailedToDebugApplicationCallback = fFailedToDebugApplicationCallback;
    oBugId.__fApplicationRunningCallback = fApplicationRunningCallback;
    oBugId.__fApplicationSuspendedCallback = fApplicationSuspendedCallback;
    oBugId.__fApplicationResumedCallback = fApplicationResumedCallback;
    oBugId.__fMainProcessTerminatedCallback = fMainProcessTerminatedCallback;
    oBugId.__fInternalExceptionCallback = fInternalExceptionCallback;
    oBugId.__fFinishedCallback = fFinishedCallback;
    
    oBugId.__oFinishedEvent = threading.Event();
    oBugId.__bStarted = False;
    # If debugging fails, this is set to a string that describes the reason why:
    oBugId.sFailedToDebugApplicationErrorMessage = None;
    # If an internal exception happens, this is set to the Exception object:
    oBugId.oInternalException = None;
    # If a bug was found, this is set to the bug report:
    oBugId.oBugReport = None;
    # Run the application in a debugger and catch exceptions.
    oBugId.__oCdbWrapper = cCdbWrapper(
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
      fFailedToDebugApplicationCallback = oBugId.__fFailedToDebugApplicationHandler,
      fApplicationRunningCallback = oBugId.__fApplicationRunningHandler,
      fApplicationSuspendedCallback = oBugId.__fApplicationSuspendedHandler,
      fApplicationResumedCallback = oBugId.__fApplicationResumedHandler,
      fMainProcessTerminatedCallback = oBugId.__fMainProcessTerminatedHandler,
      fInternalExceptionCallback = oBugId.__fInternalExceptionHandler,
      fFinishedCallback = oBugId.__fFinishedHandler,
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
    oBugId.__oCdbWrapper.fSetCheckForExcessiveCPUUsageTimeout(nTimeout);
  
  def fxSetTimeout(oBugId, nTimeout, fCallback, *axTimeoutCallbackArguments):
    return oBugId.__oCdbWrapper.fxSetTimeout(nTimeout, fCallback, *axTimeoutCallbackArguments);
  
  def fClearTimeout(oBugId, xTimeout):
    oBugId.__oCdbWrapper.fClearTimeout(xTimeout);
  
  def fnApplicationRunTime(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fnApplicationRunTime()";
    return oBugId.__oCdbWrapper.fnApplicationRunTime();
  
  def fbFinished(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fbFinished()";
    oBugId.__oFinishedEvent.isSet();
  
  # Wrap all callbacks to provide this cBugId instance as the first argument.
  def __fFailedToDebugApplicationHandler(oBugId, sErrorMessage):
    # Save error message if application cannot be debugged.
    oBugId.sFailedToDebugApplicationErrorMessage = sErrorMessage;
    oBugId.__oFinishedEvent.set();
    if oBugId.__fFailedToDebugApplicationCallback:
      oBugId.__fFailedToDebugApplicationCallback(oBugId, sErrorMessage);
  
  def  __fApplicationRunningHandler(oBugId):
    if oBugId.__fApplicationRunningCallback:
      oBugId.__fApplicationRunningCallback(oBugId);
  
  def  __fApplicationSuspendedHandler(oBugId):
    if oBugId.__fApplicationSuspendedCallback:
      oBugId.__fApplicationSuspendedCallback(oBugId);
  
  def  __fApplicationResumedHandler(oBugId):
    if oBugId.__fApplicationResumedCallback:
      oBugId.__fApplicationResumedCallback(oBugId);
  
  def __fExceptionDetectedHandler(oBugId):
    if oBugId.__fExceptionDetectedCallback:
      oBugId.__fExceptionDetectedCallback(oBugId);
  
  def __fMainProcessTerminatedHandler(oBugId):
    if oBugId.__fMainProcessTerminatedCallback:
      oBugId.__fMainProcessTerminatedCallback(oBugId);
  
  def __fInternalExceptionHandler(oBugId, oException):
    # Save internal exception.
    oBugId.oInternalException = oException;
    if oBugId.__fInternalExceptionCallback:
      oBugId.__fInternalExceptionCallback(oBugId, oException);
  
  def __fFinishedHandler(oBugId, oBugReport):
    # Save bug report, if any.
    oBugId.oBugReport = oBugReport;
    oBugId.__oFinishedEvent.set();
    if oBugId.__fFinishedCallback:
      oBugId.__fFinishedCallback(oBugId, oBugReport);

