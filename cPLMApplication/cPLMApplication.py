import os, re, sys;

from ..fasRunApplication import fasRunApplication;
from fPLMDebugHelperListenerThread import fPLMDebugHelperListenerThread;
from fNamedPipeSendData import fNamedPipeSendData;

from ..dxConfig import dxConfig;

import PLMDebugHelper;
sPLMDebugHelperPyPath = os.path.abspath(PLMDebugHelper.__file__);

class cPLMApplication(object):
  def __init__(oPLMApplication, sPackageName, sDebuggingToolsPath):
    oPLMApplication.__sPLMDebugPath = os.path.join(sDebuggingToolsPath, "plmdebug.exe");
    assert os.path.isfile(oPLMApplication.__sPLMDebugPath), \
        "Cannot find %s!" % oPLMApplication.__sPLMDebugPath;
    oPLMApplication.sPackageName = sPackageName;
    # The following values are determined on demand and cached:
    oPLMApplication.__sPackageFullName = None;
    oPLMApplication.__sPackageFamilyName = None;
    oPLMApplication.__sApplicationUserModelID = None;
  
  @property
  def sPackageFullName(oPLMApplication):
    if oPLMApplication.__sPackageFullName is None:
      oPLMApplication.__fGetPackageFullAndFamilyName();
    return oPLMApplication.__sPackageFullName;
  
  @property
  def sPackageFamilyName(oPLMApplication):
    if oPLMApplication.__sPackageFamilyName is None:
      oPLMApplication.__fGetPackageFullAndFamilyName();
    return oPLMApplication.__sPackageFamilyName;
  
  def __fGetPackageFullAndFamilyName(oPLMApplication):
    asQueryOutput = fasRunApplication("powershell", "Get-AppxPackage %s" % oPLMApplication.sPackageName);
    for sLine in asQueryOutput:
      if sLine:
        oNameAndValueMatch = re.match(r"^(.*?)\s* : (.*)$", sLine);
        assert oNameAndValueMatch, \
            "Unrecognized Get-AppxPackage output: %s\r\n%s" % (repr(sLine), "\r\n".join(asQueryOutput));
        sName, sValue = oNameAndValueMatch.groups();
        if sName == "Name":
          assert sValue.lower() == oPLMApplication.sPackageName.lower(), \
              "Expected application package name to be %s, but got %s.\r\n%s" % \
              (oPLMApplication.sPackageName, sValue, "\r\n".join(asQueryOutput));
        elif sName == "PackageFullName":
          oPLMApplication.__sPackageFullName = sValue;
        elif sName == "PackageFamilyName":
          oPLMApplication.__sPackageFamilyName = sValue;
    assert oPLMApplication.__sPackageFullName, \
        "Expected Get-AppxPackage output to contain PackageFullName value.\r\n%s" % "\r\n".join(asQueryOutput);
    assert oPLMApplication.__sPackageFamilyName, \
        "Expected Get-AppxPackage output to contain PackageFamilyName value.\r\n%s" % "\r\n".join(asQueryOutput);
  
  @property
  def sApplicationUserModelID(oPLMApplication):
    if oPLMApplication.__sApplicationUserModelID is None:
      oPLMApplication.__fGetApplicationUserModelID();
    return oPLMApplication.__sApplicationUserModelID;
  
  def __fGetApplicationUserModelID(oPLMApplication):
    # Find the application id and construct the application user model ID.
    asApplicationIds = fasRunApplication("powershell", "(Get-AppxPackageManifest %s).package.applications.application.id" % oPLMApplication.sPackageFullName);
    assert len(asApplicationIds) > 0, \
        "Expected at least one line with an id to be return by Get-AppxPackageManifest, got nothing.";
    # For now we will assume the first Id is the one we're interested in; I would not know how to determine which one
    # is best anyway...
    oPLMApplication.__sApplicationUserModelID = "%s!%s" % (oPLMApplication.sPackageFamilyName, asApplicationIds[0]);
  
  def fTerminate(oPLMApplication):
    fasRunApplication(oPLMApplication.__sPLMDebugPath, "/terminate", oPLMApplication.sPackageFullName);
  
  def fStart(oPLMApplication, oCdbWrapper):
    ############################################################################
    # Terminate the application if it is currently running.
    oPLMApplication.fTerminate();
    ############################################################################
    # Start a thread to listen for process ids send by the PLMDebug helper over
    # a named pipe and pass them to a callback:
    oPLMApplication.oPLMDebugHelperListenerThread = oCdbWrapper._foThread(fPLMDebugHelperListenerThread);
    oPLMApplication.oPLMDebugHelperListenerThread.start();
    ############################################################################
    # Ask windows to start all the applications processes suspended and run a "PLMDebugHelper" once for each
    # application process that is started. The application process' id is passed in one of the arguments to the
    # "PLMDebugHelper", which it will send back to us through a named pipe.
    # You can prefix the command line with [os.getenv("ComSpec"), "/K", "ECHO"]  to see the command
    sPLMDebugHelperCommandLine = " ".join(['"%s"' % sys.executable, sPLMDebugHelperPyPath]);
    fasRunApplication(oPLMApplication.__sPLMDebugPath, "/disableDebug", oPLMApplication.sPackageFullName);
    print fasRunApplication(oPLMApplication.__sPLMDebugPath, "/enableDebug", oPLMApplication.sPackageFullName, sPLMDebugHelperCommandLine);
    ############################################################################
    # Start the application.
    fasRunApplication("explorer.exe", "shell:AppsFolder\%s" % oPLMApplication.sApplicationUserModelID);
    # 4) BugId will start cdb once the first process' id is passed through the named pipe, attach to it and resume it.
    # 5) If another process id is passed through the named pipe, BugId will interrupt debugging to attach to it and
    #    resume the application.
    # 6) When debugging is finished, we ask windows to no longer start our "debugger" for this application.
  
  def fStopDebugging(oPLMApplication):
    # Stop the PLMDebug helper
    fasRunApplication(oPLMApplication.__sPLMDebugPath, "/disableDebug", oPLMApplication.sPackageFullName);
    # Stop the PLMDebug helper data receiving server
    try:
      fNamedPipeSendData(dxConfig["sPLMDebugHelperPipeName"], "*END*");
    except Exception, oException:
      pass;
    oPLMApplication.oPLMDebugHelperListenerThread.join();
