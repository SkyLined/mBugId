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
from mWindowsAPI import oSystemInfo, cProcessInformation;
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
    bGenerateReportHTML = False,
    uProcessMaxMemoryUse = None,
    uTotalMaxMemoryUse = None,
    uMaximumNumberOfBugs = 1,
  ):
    oBugId.__oFinishedEvent = threading.Event();
    oBugId.__bStarted = False;
    # If a bug was found, this is set to the bug report, if no bug was found, it is set to None.
    # It is not set here in order to detect when code does not properly wait for cBugId to terminate before
    # attempting to read the report.
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
      bGenerateReportHTML = bGenerateReportHTML,
      uProcessMaxMemoryUse = uProcessMaxMemoryUse,
      uTotalMaxMemoryUse = uTotalMaxMemoryUse,
      uMaximumNumberOfBugs = uMaximumNumberOfBugs,
    );
    oBugId.__oCdbWrapper.fAddEventCallback("Finished", lambda: oBugId.__oFinishedEvent.set());
    
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
  
  def fAddEventCallback(oBugId, sEventName, fCallback):
    # Wrapper for cCdbWrapper.fAddEventCallback that modifies some of the arguments passed to the callback, as we do
    # not want to expose interal objects.
    if sEventName in [
      "Application debug output", # (cProcess oProcess, str[] asOutput)
      "Failed to apply application memory limits", # (cProcess oProcess)
      "Failed to apply process memory limits", # (cProcess oProcess)
      "Page heap not enabled", # (cProcess oProcess, bool bPreventable)
      "Process attached", # (cProcess oProcess)
      "Process terminated", #(cProcess oProcess)
    ]:
      # These get a cProcess instance as their second argument from cCdbWrapper, which is an internal object that we
      # do not want to expose. We'll create a mWindowsAPI.cProcessInformation object for the process and pass that as
      # the first argument to the callback instead. We'll also insert a boolean that indicates if the process is a
      # main process.
      fOriginalCallback = fCallback;
      fCallback = lambda oBugId, oProcess, *axArguments: fOriginalCallback(
        oBugId, 
        cProcessInformation.foGetForId(oProcess.uId),
        oProcess.uId in oBugId.__oCdbWrapper.auMainProcessIds, # bIsMainProcess
        *axArguments
      );
    if sEventName in [
      "Application stderr output", # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Application stdout output", # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Process started", # (mWindowsAPI.cConsoleProcess oConsoleProcess)
    ]:
      # These get a cConsoleProcess instance as their second argument from cCdbWrapper, which we'll use to find out
      # if the process is a main process and insert that as a boolean as the second argument:
      # to the callback instead.
      fOriginalCallback = fCallback;
      fCallback = lambda oBugId, oConsoleProcess, *axArguments: fOriginalCallback(
        oBugId, 
        oConsoleProcess,
        oConsoleProcess.uId in oBugId.__oCdbWrapper.auMainProcessIds, # bIsMainProcess
        *axArguments
      );
    return oBugId.__oCdbWrapper.fAddEventCallback(
      sEventName,
      lambda *axArguments: fCallback(oBugId, *axArguments),
    );
  