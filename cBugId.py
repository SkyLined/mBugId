import os, sys;

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

# Actually load the stuff from external modules that we need.
from mWindowsAPI import oSystemInfo, cUWPApplication;
from mMultiThreading import cLock;
from mNotProvided import *;

from .cCdbWrapper import cCdbWrapper;
from .dxConfig import dxConfig;

class cBugId(object):
  # This is not much more than a wrapper for cCdbWrapper which hides internal
  # functions and only exposes those things that should be exposed:
  sOSISA = oSystemInfo.sOSISA;
  dxConfig = dxConfig; # Expose so external scripts can modify
  
  @classmethod
  def fbCdbFound(oSelf, sCdbISA):
    # Returns True if cdb.exe is found in the path to the Debugging Tools for Windows as specified in dxConfig.
    return (
      dxConfig["sDebuggingToolsPath_%s" % sCdbISA]
      and os.path.isfile(os.path.join(dxConfig["sDebuggingToolsPath_%s" % sCdbISA], "cdb.exe"))
    );
  
  def __init__(oBugId,
    sCdbISA = None, # Which version of cdb should be used to debug this application? Try not to use; could lead to bad bug reports!
    s0ApplicationBinaryPath = None,
    a0uApplicationProcessIds = None,
    u0JITDebuggerEventId = None,
    o0UWPApplication = None,
    asApplicationArguments = [],
    asLocalSymbolPaths = [],
    azsSymbolCachePaths = zNotProvided, 
    azsSymbolServerURLs = zNotProvided,
    d0sURLTemplate_by_srSourceFilePath = None,
    bGenerateReportHTML = False,
    u0ProcessMaxMemoryUse = None,
    u0TotalMaxMemoryUse = None,
    uMaximumNumberOfBugs = 1,
  ):
    fAssertTypes({
      "sCdbISA": (sCdbISA, str),
      "s0ApplicationBinaryPath": (s0ApplicationBinaryPath, str, None),
      "a0uApplicationProcessIds": (a0uApplicationProcessIds, [int], None),
      "u0JITDebuggerEventId": (u0JITDebuggerEventId, int, None),
      "o0UWPApplication": (o0UWPApplication, cUWPApplication, None),
      "asApplicationArguments": (asApplicationArguments, [str]),
      "asLocalSymbolPaths": (asLocalSymbolPaths, [str]),
      "azsSymbolCachePaths": (azsSymbolCachePaths, [str], zNotProvided), 
      "azsSymbolServerURLs": (azsSymbolServerURLs, [str], zNotProvided),
      "d0sURLTemplate_by_srSourceFilePath": (d0sURLTemplate_by_srSourceFilePath, dict, None),
      "bGenerateReportHTML": (bGenerateReportHTML, bool),        
      "u0ProcessMaxMemoryUse": (u0ProcessMaxMemoryUse, int, None),
      "u0TotalMaxMemoryUse": (u0TotalMaxMemoryUse, int, None),
      "uMaximumNumberOfBugs": (uMaximumNumberOfBugs, int),
    });
    oBugId.__oRunningLock = cLock(bLocked = True);
    oBugId.__bStarted = False;
    oBugId.o0UWPApplication = o0UWPApplication;
    # If a bug was found, this is set to the bug report, if no bug was found, it is set to None.
    # It is not set here in order to detect when code does not properly wait for cBugId to terminate before
    # attempting to read the report.
    # Run the application in a debugger and catch exceptions.
    oBugId.__oCdbWrapper = cCdbWrapper(
      sCdbISA = sCdbISA,
      s0ApplicationBinaryPath = s0ApplicationBinaryPath,
      a0uApplicationProcessIds = a0uApplicationProcessIds,
      u0JITDebuggerEventId = u0JITDebuggerEventId,
      o0UWPApplication = oBugId.o0UWPApplication,
      asApplicationArguments = asApplicationArguments,
      asLocalSymbolPaths = asLocalSymbolPaths,
      azsSymbolCachePaths = azsSymbolCachePaths,
      azsSymbolServerURLs = azsSymbolServerURLs,
      d0sURLTemplate_by_srSourceFilePath = d0sURLTemplate_by_srSourceFilePath,
      bGenerateReportHTML = bGenerateReportHTML,
      u0ProcessMaxMemoryUse = u0ProcessMaxMemoryUse,
      u0TotalMaxMemoryUse = u0TotalMaxMemoryUse,
      uMaximumNumberOfBugs = uMaximumNumberOfBugs,
    );
    # Once we're done, release the "running" lock
    oBugId.__oCdbWrapper.fAddCallback("Finished", lambda oCdbWrapper:
      oBugId.__oRunningLock.fRelease()
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
    assert oBugId.__oRunningLock, \
        "You cannot call fWait twice";
    oBugId.__oRunningLock.fWait();
    oBugId.__oRunningLock = None; # Make sure no further fWait calls can be made.
  
  def fSetCheckForExcessiveCPUUsageTimeout(oBugId, nTimeoutInSeconds):
    oBugId.__oCdbWrapper.fSetCheckForExcessiveCPUUsageTimeout(nTimeoutInSeconds);
  def fCheckForExcessiveCPUUsage(oBugId, fCallback):
    return oBugId.__oCdbWrapper.fCheckForExcessiveCPUUsage(lambda bExcessiveCPUUsageDetected: fCallback(oBugId, bExcessiveCPUUsageDetected));
  
  def foSetTimeout(oBugId, sDescription, nTimeoutInSeconds, f0Callback, *txCallbackArguments):
    return oBugId.__oCdbWrapper.foSetTimeout(
      sDescription,
      nTimeoutInSeconds,
      lambda oCdbWrapper, *txArguments: f0Callback(oBugId, *txArguments) # replace oCdbWrapper with oBugId
          if f0Callback else None,
    );
  
  def fClearTimeout(oBugId, oTimeout):
    oBugId.__oCdbWrapper.fClearTimeout(oTimeout);
  
  def fnApplicationRunTimeInSeconds(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fnApplicationRunTimeInSeconds()";
    return oBugId.__oCdbWrapper.nApplicationRunTimeInSeconds;
  
  def fAttachForProcessExecutableNames(oBugId, *asBinaryNames):
    return oBugId.__oCdbWrapper.fQueueAttachForProcessExecutableNames(*asBinaryNames);
  
  def fbFinished(oBugId):
    assert oBugId.__bStarted is True, \
        "You must call cBugId.fStart() before calling cBugId.fbFinished()";
    return oBugId.__oFinishedEvent.isSet();
  
  def fAddCallback(oBugId, sEventName, fCallback):
    # Wrapper for cCdbWrapper.fAddCallback that modifies some of the arguments passed to the callback, as we do
    # not want to expose interal objects. A lot of this should actually be done in the relevant `fbFireCallbacks` calls, 
    # but this was not possible before.
    if sEventName in [
      "Application debug output", # (cProcess oProcess, str[] asOutput)
      "ASan detected", # (cProcess oProcess)
      "Failed to apply application memory limits", # (cProcess oProcess)
      "Failed to apply process memory limits", # (cProcess oProcess)
      "Page heap not enabled", # (cProcess oProcess, bool bPreventable)
      "Cdb ISA not ideal", # (cProcess oProcess, str sCdbISA, bool bPreventable)
      "Process attached", # (cProcess oProcess)
      "Process terminated", #(cProcess oProcess)
    ]:
      # These get a cProcess instance as their second argument from cCdbWrapper, which is an internal object that we
      # do not want to expose. We'll retreive the associated mWindowsAPI.cProcess object and pass that as the second
      # argument to the callback instead. We'll also insert a boolean that indicates if the process is a main process.
      fOriginalCallback = fCallback;
      fCallback = lambda oCdbWrapper, oProcess, *txArguments: fOriginalCallback(
        oBugId, 
        oProcess.oWindowsAPIProcess,
        oProcess.uId in oBugId.__oCdbWrapper.auMainProcessIds, # bIsMainProcess
        *txArguments
      );
    if sEventName in [
      "Application stderr output", # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Application stdout output", # (mWindowsAPI.cConsoleProcess oConsoleProcess, str sOutput)
      "Process started", # (mWindowsAPI.cConsoleProcess oConsoleProcess)
    ]:
      # These get a cConsoleProcess instance as their second argument from cCdbWrapper, which we'll use to find out
      # if the process is a main process and insert that as a boolean as the third argument:
      # to the callback instead.
      fOriginalCallback = fCallback;
      fCallback = lambda oCdbWrapper, oConsoleProcess, *txArguments: fOriginalCallback(
        oBugId, 
        oConsoleProcess,
        oConsoleProcess.uId in oBugId.__oCdbWrapper.auMainProcessIds, # bIsMainProcess
        *txArguments
      );
    return oBugId.__oCdbWrapper.fAddCallback(
      sEventName,
      lambda oCdbWrapper, *txArguments: fCallback(oBugId, *txArguments), # replace oCdbWrapper with oBugId
    );
  
  def fSaveDumpToFile(oBugId, sFilePath, bOverwrite, bFull):
    return oBugId.__oCdbWrapper.fSaveDumpToFile(sFilePath, bOverwrite, bFull);

