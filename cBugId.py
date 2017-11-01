import os, sys, threading;

"""
                          __                     _____________                  
            ,,,     _,siSS**SSis,_        ,-.   /             |                 
           :O()   ,SP*'`      `'*YS,     |   `-|  O    BugId  |                 
            ```  dS'  _    |    _ 'Sb   ,'      \_____________|                 
      ,,,       dP     \,-` `-<`    Yb _&/                                      
     :O()      ,S`  \,' \      \    `Sis|ssssssssssssssssss,        ,,,         
      ```      (S   (   | --====)    SSS|SSSSSSSSSSSSSSSSSSD        ()O:        
               'S,  /', /      /    ,S?*/******************'        ```         
                Yb    _/'-_ _-<._   dP `                                        
  _______________YS,       |      ,SP_________________________________________  
                  `Sbs,_      _,sdS`                                            
                    `'*YSSssSSY*'`                   https://bugid.skylined.nl  
                          ``                                                    
                                                                                
""";

# Augment the search path: look in main folder, parent folder or "modules" child folder, in that order.
sMainFolderPath = os.path.abspath(os.path.dirname(__file__));
sParentFolderPath = os.path.normpath(os.path.join(sMainFolderPath, ".."));
sModuleFolderPath = os.path.join(sMainFolderPath, "modules");
asAbsoluteLoweredSysPaths = [os.path.abspath(sPath).lower() for sPath in sys.path];
sys.path += [sPath for sPath in [
  sMainFolderPath,
  sParentFolderPath,
  sModuleFolderPath,
] if sPath.lower() not in asAbsoluteLoweredSysPaths];

for (sModule, sURL) in {
  "mWindowsAPI": "https://github.com/SkyLined/mWindowsAPI/",
  "mFileSystem": "https://github.com/SkyLined/mFileSystem/",
}.items():
  try:
    __import__(sModule, globals(), locals(), [], -1);
  except ImportError, oError:
    if oError.message == "No module named %s" % sModuleName:
      print "*" * 80;
      print "cBugId depends on %s which you can download at:" % sModuleName;
      print "    %s" % sDownloadURL;
      print "After downloading, please save the code in this folder:";
      print "    %s" % os.path.join(sModuleFolderPath, sModuleName);
      print " - or -";
      print "    %s" % os.path.join(sParentFolderPath, sModuleName);
      print "Once you have completed these steps, please try again.";
      print "*" * 80;
    raise;

from cCdbWrapper import cCdbWrapper;
from oVersionInformation import oVersionInformation;
from mWindowsAPI import fsGetOSISA;
from dxConfig import dxConfig;

class cBugId(object):
  # This is not much more than a wrapper for cCdbWrapper which hides internal
  # functions and only exposes those things that should be exposed:
  oVersionInformation = oVersionInformation;
  sOSISA = fsGetOSISA();
  dxConfig = dxConfig; # Expose so external scripts can modify
  
  def __init__(oBugId,
    sCdbISA = None, # Which version of cdb should be used to debug this application?
    sApplicationBinaryPath = None,
    auApplicationProcessIds = None,
    sApplicationPackageName = None,
    sApplicationId = None,
    asApplicationArguments = None,
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
    fPageHeapNotEnabledCallback = None,
    fStdInInputCallback = None,
    fStdOutOutputCallback = None,
    fStdErrOutputCallback = None,
    fNewProcessCallback = None,
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
    oBugId.__fPageHeapNotEnabledCallback = fPageHeapNotEnabledCallback;
    oBugId.__fStdInInputCallback = fStdInInputCallback;
    oBugId.__fStdOutOutputCallback = fStdOutOutputCallback;
    oBugId.__fStdErrOutputCallback = fStdErrOutputCallback;
    oBugId.__fNewProcessCallback = fNewProcessCallback;
    
    oBugId.__oFinishedEvent = threading.Event();
    oBugId.__bStarted = False;
    # If a bug was found, this is set to the bug report, if no bug was found, it is set to None.
    # It is not set here in order to detect when code does not properly wait for cBugId to terminate before
    # attempting to read the report.
    # oBugId.oBugReport = None;
    # Run the application in a debugger and catch exceptions.
    oBugId.__oCdbWrapper = cCdbWrapper(
      sCdbISA = sCdbISA,
      sApplicationBinaryPath = sApplicationBinaryPath,
      auApplicationProcessIds = auApplicationProcessIds,
      sApplicationPackageName = sApplicationPackageName,
      sApplicationId = sApplicationId,
      asApplicationArguments = asApplicationArguments,
      asLocalSymbolPaths = asLocalSymbolPaths,
      asSymbolCachePaths = asSymbolCachePaths,
      asSymbolServerURLs = asSymbolServerURLs,
      dsURLTemplate_by_srSourceFilePath = dsURLTemplate_by_srSourceFilePath,
      rImportantStdOutLines = rImportantStdOutLines,
      rImportantStdErrLines = rImportantStdErrLines,
      bGenerateReportHTML = bGenerateReportHTML,
      # All callbacks are wrapped to insert this cBugId instance as the first argument.
      fFailedToDebugApplicationCallback = oBugId.__fFailedToDebugApplicationHandler,
      fApplicationRunningCallback = oBugId.__fApplicationRunningCallback and \
          (lambda: oBugId.__fApplicationRunningCallback(oBugId)),
      fApplicationSuspendedCallback = oBugId.__fApplicationSuspendedCallback and \
          (lambda sReason: oBugId.__fApplicationSuspendedCallback(oBugId, sReason)),
      fApplicationResumedCallback = oBugId.__fApplicationResumedCallback and \
          (lambda: oBugId.__fApplicationResumedCallback(oBugId)),
      fMainProcessTerminatedCallback = oBugId.__fMainProcessTerminatedCallback and \
          (lambda uProcessId, sBinaryName: oBugId.__fMainProcessTerminatedCallback(oBugId, uProcessId, sBinaryName)),
      fInternalExceptionCallback = oBugId.__fInternalExceptionCallback and \
          (lambda oException, oTraceBack: oBugId.__fInternalExceptionCallback(oBugId, oException, oTraceBack)),
      fFinishedCallback = oBugId.__fFinishedHandler,
      fPageHeapNotEnabledCallback = oBugId.__fPageHeapNotEnabledCallback and \
          (lambda uProcessId, sBinaryName, bPreventable: oBugId.__fPageHeapNotEnabledCallback(oBugId, uProcessId, sBinaryName, bPreventable)),
      fStdInInputCallback = oBugId.__fStdInInputCallback and \
          (lambda sInput: oBugId.__fStdInInputCallback(oBugId, sInput)),
      fStdOutOutputCallback = oBugId.__fStdOutOutputCallback and \
          (lambda sOutput: oBugId.__fStdOutOutputCallback(oBugId, sOutput)),
      fStdErrOutputCallback = oBugId.__fStdErrOutputCallback and \
          (lambda sOutput: oBugId.__fStdErrOutputCallback(oBugId, sOutput)),
      fNewProcessCallback = oBugId.__fNewProcessCallback and \
          (lambda oProcess: oBugId.__fNewProcessCallback(oBugId, oProcess)),
    );
  
  @property
  def aoInternalExceptions(oBugId):
    return oBugId.__oCdbWrapper.aoInternalExceptions[:];
  
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
  
  def foSetTimeout(oBugId, sDescription, nTimeout, fCallback, *axTimeoutCallbackArguments):
    # The first argument of any callback on cBugId is the oBugId instance; add it:
    axTimeoutCallbackArguments = [oBugId] + list(axTimeoutCallbackArguments);
    return oBugId.__oCdbWrapper.foSetTimeout(sDescription, nTimeout, fCallback, *axTimeoutCallbackArguments);
  
  def fClearTimeout(oBugId, oTimeout):
    oBugId.__oCdbWrapper.fClearTimeout(oTimeout);
  
  def fnApplicationRunTime(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fnApplicationRunTime()";
    return oBugId.__oCdbWrapper.nApplicationRunTime;
  
  def fAttachToProcessesForExecutableNames(oBugId, *asBinaryNames):
    return oBugId.__oCdbWrapper.fAttachToProcessesForExecutableNames(*asBinaryNames);
  
  def fbFinished(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fbFinished()";
    return oBugId.__oFinishedEvent.isSet();
  
  def __fFailedToDebugApplicationHandler(oBugId, sErrorMessage):
    oBugId.oBugReport = None;
    oBugId.__oFinishedEvent.set();
    # This error must be handled, or an assertion is thrown
    assert oBugId.__fFailedToDebugApplicationCallback, sErrorMessage;
    oBugId.__fFailedToDebugApplicationCallback(oBugId, sErrorMessage);
  
  def __fFinishedHandler(oBugId, oBugReport):
    # Save bug report, if any.
    oBugId.oBugReport = oBugReport;
    oBugId.__oFinishedEvent.set();
    if oBugId.__fFinishedCallback:
      oBugId.__fFinishedCallback(oBugId, oBugReport);
