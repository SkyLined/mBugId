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
sMainFolderPath = os.path.dirname(os.path.abspath(__file__));
sParentFolderPath = os.path.normpath(os.path.join(sMainFolderPath, ".."));
sModuleFolderPath = os.path.join(sMainFolderPath, "modules");
asAbsoluteLoweredSysPaths = [os.path.abspath(sPath).lower() for sPath in sys.path];
sys.path += [sPath for sPath in [
  sMainFolderPath,
  sParentFolderPath,
  sModuleFolderPath,
] if sPath.lower() not in asAbsoluteLoweredSysPaths];

for (sModuleName, sURL) in {
  "mWindowsAPI": "https://github.com/SkyLined/mWindowsAPI/",
  "mFileSystem": "https://github.com/SkyLined/mFileSystem/",
}.items():
  try:
    __import__(sModuleName, globals(), locals(), [], -1);
  except ImportError as oError:
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
from mWindowsAPI import oSystemInfo;
from dxConfig import dxConfig;

class cBugId(object):
  # This is not much more than a wrapper for cCdbWrapper which hides internal
  # functions and only exposes those things that should be exposed:
  oVersionInformation = oVersionInformation;
  sOSISA = oSystemInfo.sOSISA;
  dxConfig = dxConfig; # Expose so external scripts can modify
  
  def __init__(oBugId,
    sCdbISA = None, # Which version of cdb should be used to debug this application?
    sApplicationBinaryPath = None,
    auApplicationProcessIds = None,
    sUWPApplicationPackageName = None,
    sUWPApplicationId = None,
    asApplicationArguments = None,
    asLocalSymbolPaths = None,
    asSymbolCachePaths = None, 
    asSymbolServerURLs = None,
    dsURLTemplate_by_srSourceFilePath = None,
    rImportantStdOutLines = None,
    rImportantStdErrLines = None,
    bGenerateReportHTML = False,
    uProcessMaxMemoryUse = None,
    uTotalMaxMemoryUse = None,
    fFailedToDebugApplicationCallback = None,
    fFailedToApplyMemoryLimitsCallback = None,
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
    fLogMessageCallback = None,
    fApplicationStdOutOrErrOutputCallback = None,
  ):
    oBugId.__fFailedToDebugApplicationCallback = fFailedToDebugApplicationCallback;
    oBugId.__fFinishedCallback = fFinishedCallback;
    
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
      sUWPApplicationPackageName = sUWPApplicationPackageName,
      sUWPApplicationId = sUWPApplicationId,
      asApplicationArguments = asApplicationArguments,
      asLocalSymbolPaths = asLocalSymbolPaths,
      asSymbolCachePaths = asSymbolCachePaths,
      asSymbolServerURLs = asSymbolServerURLs,
      dsURLTemplate_by_srSourceFilePath = dsURLTemplate_by_srSourceFilePath,
      rImportantStdOutLines = rImportantStdOutLines,
      rImportantStdErrLines = rImportantStdErrLines,
      bGenerateReportHTML = bGenerateReportHTML,
      uProcessMaxMemoryUse = uProcessMaxMemoryUse,
      uTotalMaxMemoryUse = uTotalMaxMemoryUse,
      # All callbacks are wrapped to insert this cBugId instance as the first argument.
      fFailedToDebugApplicationCallback = oBugId.__fFailedToDebugApplicationHandler,
      fFailedToApplyMemoryLimitsCallback = lambda oProcess: fFailedToApplyMemoryLimitsCallback and \
          fFailedToApplyMemoryLimitsCallback(oBugId, oProcess.uId, oProcess.sBinaryName, oProcess.sCommandLine),
      fApplicationRunningCallback = lambda: fApplicationRunningCallback and \
          fApplicationRunningCallback(oBugId),
      fApplicationSuspendedCallback = lambda sReason: fApplicationSuspendedCallback and \
          fApplicationSuspendedCallback(oBugId, sReason),
      fApplicationResumedCallback = lambda: fApplicationResumedCallback and \
          fApplicationResumedCallback(oBugId),
      fMainProcessTerminatedCallback = lambda oProcess: fMainProcessTerminatedCallback and \
          fMainProcessTerminatedCallback(oBugId, oProcess.uId, oProcess.sBinaryName, oProcess.sCommandLine),
      fInternalExceptionCallback = lambda oException, oTraceBack: fInternalExceptionCallback and \
          fInternalExceptionCallback(oBugId, oException, oTraceBack),
      fFinishedCallback = oBugId.__fFinishedHandler,
      fPageHeapNotEnabledCallback = lambda oProcess, bPreventable: fPageHeapNotEnabledCallback and \
          fPageHeapNotEnabledCallback(oBugId, oProcess.uId, oProcess.sBinaryName, oProcess.sCommandLine, bPreventable),
      fStdInInputCallback = lambda sInput: fStdInInputCallback and \
          fStdInInputCallback(oBugId, sInput),
      fStdOutOutputCallback = lambda sOutput: fStdOutOutputCallback and \
          fStdOutOutputCallback(oBugId, sOutput),
      fStdErrOutputCallback = lambda sOutput: fStdErrOutputCallback and 
          fStdErrOutputCallback(oBugId, sOutput),
      fNewProcessCallback = lambda oProcess: fNewProcessCallback and \
          fNewProcessCallback(oBugId, oProcess.uId, oProcess.sBinaryName, oProcess.sCommandLine),
      fLogMessageCallback = lambda sMessageClass, sMessage: fLogMessageCallback and \
          fLogMessageCallback(oBugId, sMessageClass, sMessage),
      fApplicationStdOutOrErrOutputCallback = lambda uProcessId, sBinaryName, sCommandLine, sStdOutOrErr, sMessage: \
          fApplicationStdOutOrErrOutputCallback and \
          fApplicationStdOutOrErrOutputCallback(oBugId, uProcessId, sBinaryName, sCommandLine, sStdOutOrErr, sMessage),
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
    # This error must be handled, or an assertion is thrown
    assert oBugId.__fFailedToDebugApplicationCallback, sErrorMessage;
    oBugId.__fFailedToDebugApplicationCallback(oBugId, sErrorMessage);
  
  def __fFinishedHandler(oBugId, oBugReport):
    # Save bug report, if any.
    oBugId.oBugReport = oBugReport;
    oBugId.__oFinishedEvent.set();
    if oBugId.__fFinishedCallback:
      oBugId.__fFinishedCallback(oBugId, oBugReport);
