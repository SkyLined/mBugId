import os, platform, re, sys, threading, time, traceback;

# Augment the search path to make cBugId a package and have access to its modules folder.
sTestsFolderPath = os.path.dirname(os.path.abspath(__file__));
sMainFolderPath = os.path.dirname(sTestsFolderPath);
sParentFolderPath = os.path.dirname(sMainFolderPath);
sModulesFolderPath = os.path.join(sMainFolderPath, "modules");
asOriginalSysPath = sys.path[:];
sys.path = [sParentFolderPath, sModulesFolderPath] + asOriginalSysPath;
# Save the list of names of loaded modules:
asOriginalModuleNames = sys.modules.keys();

import cBugId, mFileSystem, mWindowsAPI;

# Restore the search path
sys.path = asOriginalSysPath;

# Sub-packages should load all modules relative, or they will end up in the global namespace, which means they may get
# loaded by the script importing it if it tries to load a differnt module with the same name. Obviously, that script
# will probably not function when the wrong module is loaded, so we need to check that we did this correctly.
for sModuleName in sys.modules.keys():
  assert (
    sModuleName in asOriginalModuleNames # This was loaded before cBugId was loaded
    or sModuleName.lstrip("_").split(".", 1)[0] in [
      "cBugId", # This was loaded as part of the cBugId package
      # These packages are loaded by cBugId:
      "mWindowsAPI", "mFileSystem", "mProductDetails",
      # These built-in modules are loaded by these packages:
      "base64", "binascii", "bz2", "contextlib", "cStringIO", "ctypes", "datetime", "encodings", "fnmatch", "gc",
      "hashlib", "hmac", "json", "math", "msvcrt", "nturl2path", "shutil", "socket", "ssl", "struct", "subprocess",
      "textwrap", "urllib", "urlparse", "winreg", "zlib",
    ]
  ), \
      "Module %s was unexpectedly loaded outside of the cBugId package!" % sModuleName;

from cBugId import cBugId;
from cBugId.mAccessViolation.fbUpdateReportForSpecialPointer import gddtsDetails_uSpecialAddress_sISA;
from mFileSystem import mFileSystem;
from mWindowsAPI import oSystemInfo;
from mWindowsAPI.mDefines import *;
from mWindowsAPI.mDLLs import KERNEL32;
from mWindowsAPI.mFunctions import *;

gbDebugStartFinish = False;  # Show some output when a test starts and finishes.
gbShowCdbIO = False;          # Show cdb I/O during tests (you'll want to run only 1 test at a time for this).
gbShowApplicationIO = False;
gbLicenseWarningsShown = False;

dsComSpec_by_sISA = {};
dsComSpec_by_sISA[oSystemInfo.sOSISA] = os.path.join(os.environ.get("WinDir"), "System32", "cmd.exe");
if oSystemInfo.sOSISA == "x64":
  dsComSpec_by_sISA["x86"] = os.path.join(os.environ.get("WinDir"), "SysWOW64", "cmd.exe");

cBugId.dxConfig["bShowAllCdbCommandsInReport"] = True;
cBugId.dxConfig["nExcessiveCPUUsageCheckInterval"] = 1; # The test application is simple: CPU usage should be apparent after a few seconds.
cBugId.dxConfig["uArchitectureIndependentBugIdBits"] = 32; # Test architecture independent bug ids

sPythonISA = {
  "32bit": "x86",
  "64bit": "x64",
}[platform.architecture()[0]];
asTestISAs = {
  "x86": ["x86"],
  "x64": ["x64", "x86"],
}[sPythonISA];

sReportsFolderName = mFileSystem.fsPath(sTestsFolderPath, "Reports");

dsBinaries_by_sISA = {
  "x86": os.path.join(sTestsFolderPath, "bin", "Tests_x86.exe"),
  "x64": os.path.join(sTestsFolderPath, "bin", "Tests_x64.exe"),
};

bFailed = False;
gbGenerateReportHTML = False;
oOutputLock = threading.Lock();
guTotalMaxMemoryUse =  0x01234567; # The test application memory use limit: it should be large enough to allow the test
                                   # to function, but small enough to detect excessive memory use before the entire
                                   # system runs low on memory.
guOOMAllocationBlockSize = 0x1234; # The out-of-memory test allocations size. it should be large enough to cause OOM
                                   # reasonably fast, but small enough so a not to hit the guTotalMaxMemoryUse
                                   # immediately, as this would not represent a normal OOM scenario.
guLargeHeapBlockSize = 0x00800000; # Should be large to detect potential issues when handling large allocations, but
                                   # not so large as to cause the application to allocate more memory than it is allowed
                                   # through the guTotalMaxMemoryUse variable.

guLastLineLength = 0;
def fOutput(sMessage = "", bCRLF = True):
  global guLastLineLength;
  oOutputLock and oOutputLock.acquire();
  sPaddedMessage = sMessage.ljust(guLastLineLength);
  if bCRLF:
    print sPaddedMessage;
    guLastLineLength = 0;
  else:
    print (sPaddedMessage + "\r"),;
    guLastLineLength = len(sMessage);
  oOutputLock and oOutputLock.release();

def fSetTitle(sTitle):
  assert KERNEL32.SetConsoleTitleW(sTitle), \
      "SetConsoleTitleW(%s) => Error %08X" % \
      (repr(sTitle), KERNEL32.GetLastError());
  
gbTestFailed = False;

def fTest(
  sISA,
  axCommandLineArguments,
  asExpectedBugIdAndLocations,
  sExpectedFailedToDebugApplicationErrorMessage = None,
  bRunInShell = False,
  sApplicationBinaryPath = None,
  uMaximumNumberOfBugs = 2,
  bExcessiveCPUUsageChecks = False,
):
  global gbTestFailed;
  if gbTestFailed:
    return;
  asApplicationArguments = axCommandLineArguments and [
    isinstance(x, str) and x
             or x < 10 and ("%d" % x)
                        or ("0x%X" % x)
    for x in axCommandLineArguments
  ] or [];
  if sApplicationBinaryPath is None:
    sApplicationBinaryPath = dsBinaries_by_sISA[sISA];
  asCommandLine = [sApplicationBinaryPath] + asApplicationArguments;
  sFailedToDebugApplicationErrorMessage = None;
  if sExpectedFailedToDebugApplicationErrorMessage:
    sTestDescription = "%s => %s" % ("Running %s" % sApplicationBinaryPath, repr(sExpectedFailedToDebugApplicationErrorMessage));
  else:
    sTestDescription = "%s %s%s => %s" % (
      sISA,
      " ".join(asApplicationArguments), \
      bRunInShell and " (in child process)" or "",
      asExpectedBugIdAndLocations and " => ".join(asExpectedBugIdAndLocations) or "no bugs");
  
  sTestBinaryName = os.path.basename(sApplicationBinaryPath).lower();
  
  if bRunInShell:
    asApplicationArguments = ["/C", sApplicationBinaryPath] + asApplicationArguments; 
    sApplicationBinaryPath = dsComSpec_by_sISA[sISA];
  
  fSetTitle(sTestDescription);
  if gbDebugStartFinish:
    fOutput("* Started %s" % sTestDescription);
  else:
    fOutput("* %s" % sTestDescription, bCRLF = False);
  
  asLog = [];
  def fCdbStdInInputCallback(oBugId, sInput):
    if gbShowCdbIO: fOutput("stdin<%s" % sInput);
    asLog.append("stdin<%s" % sInput);
  def fCdbStdOutOutputCallback(oBugId, sOutput):
    if gbShowCdbIO: fOutput("stdout>%s" % sOutput);
    asLog.append("stdout>%s" % sOutput);
  def fCdbStdErrOutputCallback(oBugId, sOutput):
    if gbShowCdbIO: fOutput("stderr>%s" % sOutput);
    asLog.append("stderr>%s" % sOutput);
#    asLog.append("log>%s%s" % (sMessage, sData and " (%s)" % sData or ""));
  def fApplicationDebugOutputCallback(oBugId, oProcessInformation, bIsMainProcess, asOutput):
    bFirstLine = True;
    for sOutput in asOutput:
      sLogLine = "%s process %d/0x%X (%s): %s>%s" % (bIsMainProcess and "Main" or "Sub", oProcessInformation.uId, \
          oProcessInformation.uId, oProcessInformation.sBinaryName, bFirstLine and "debug" or "     ", sOutput);
      if gbShowApplicationIO: fOutput(sLogLine);
      asLog.append(sLogLine);
      bFirstLine = False;
  def fApplicationStdErrOutputCallback(oBugId, oConsoleProcess, bIsMainProcess, sOutput):
    # This is always a main process
    sLogLine = "%s process %d/0x%X (%s): stderr> %s" % (bIsMainProcess and "Main" or "Sub", oConsoleProcess.uId, \
        oConsoleProcess.uId, oConsoleProcess.sBinaryName, sOutput);
    if gbShowApplicationIO: fOutput(sLogLine);
    asLog.append(sLogLine);
  def fApplicationStdOutOutputCallback(oBugId, oConsoleProcess, bIsMainProcess, sOutput):
    # This is always a main process
    sLogLine = "%s process %d/0x%X (%s): stdout> %s" % (bIsMainProcess and "Main" or "Sub", oConsoleProcess.uId, \
        oConsoleProcess.uId, oConsoleProcess.sBinaryName, sOutput)
    if gbShowApplicationIO: fOutput(sLogLine);
    asLog.append(sLogLine);
  def fApplicationSuspendedCallback(oBugId, sReason):
    asLog.append("Application suspended (%s)" % sReason);
  def fApplicationResumedCallback(oBugId):
    asLog.append("Application resumed");
  def fApplicationRunningCallback(oBugId):
    asLog.append("Application running");
  def fFailedToDebugApplicationCallback(oBugId, sErrorMessage):
    global gbTestFailed;
    if sExpectedFailedToDebugApplicationErrorMessage == sErrorMessage:
      return;
    gbTestFailed = True;
    if not gbShowCdbIO: 
      for sLine in asLog:
        fOutput(sLine);
    fOutput("- Failed test: %s" % sTestDescription);
    if sExpectedFailedToDebugApplicationErrorMessage:
      fOutput("  Expected:    %s" % repr(sExpectedFailedToDebugApplicationErrorMessage));
    else:
      fOutput("  BugId unexpectedly failed to debug the application");
    fOutput("  Error:       %s" % repr(sErrorMessage));
    oBugId.fStop();
  def fFailedToApplyMemoryLimitsCallback(oBugId, oProcessInformation):
    global gbTestFailed;
    gbTestFailed = True;
    if not gbShowCdbIO: 
      for sLine in asLog:
        fOutput(sLine);
    fOutput("- Failed to apply memory limits to process %d/0x%X (%s: %s) for test: %s" % (oProcessInformation.uId, \
        oProcessInformation.uId, oProcessInformation.sBinaryName, oProcessInformation.sCommandLine, sTestDescription));
    oBugId.fStop();
  def fFinishedCallback(oBugId):
    if gbShowCdbIO: fOutput("Finished");
    asLog.append("Finished");
  def fLicenseWarningsCallback(oBugId, asLicenseWarnings):
    global gbLicenseWarningsShown;
    if not gbLicenseWarningsShown:
      fOutput("@" * 80);
      for sLicenseWarning in asLicenseWarnings:
        fOutput("@ %s" % sLicenseWarning);
      fOutput("@" * 80);
      gbLicenseWarningsShown = True;
  def fLicenseErrorsCallback(oBugId, asLicenseErrors):
    fOutput("@" * 80);
    for sLicenseError in asLicenseErrors:
      fOutput("@ %s" % sLicenseError);
    fOutput("@" * 80);
    os._exit(1);
  
  def fInternalExceptionCallback(oBugId, oException, oTraceBack):
    global gbTestFailed;
    gbTestFailed = True;
    if not gbShowCdbIO: 
      for sLine in asLog:
        fOutput(sLine);
    fOutput("@" * 80);
    fOutput("- An internal exception has occured in test: %s" % sTestDescription);
    fOutput("  %s" % repr(oException));
    fOutput("  Stack:");
    txStack = traceback.extract_tb(oTraceBack);
    uFrameIndex = len(txStack) - 1;
    for (sFileName, uLineNumber, sFunctionName, sCode) in reversed(txStack):
      sSource = "%s/%d" % (sFileName, uLineNumber);
      if sFunctionName != "<module>":
        sSource = "%s (%s)" % (sFunctionName, sSource);
      fOutput("  %3d %s" % (uFrameIndex, sSource));
      if sCode:
        fOutput("      > %s" % sCode.strip());
      uFrameIndex -= 1;
    fOutput("@" * 80);
    oBugId.fStop();
  def fPageHeapNotEnabledCallback(oBugId, oProcessInformation, bIsMainProcess, bPreventable):
    assert oProcessInformation.sBinaryName == "cmd.exe", \
        "It appears you have not enabled page heap for %s, which is required to run tests." % sBinaryName;
  def fProcessAttachedCallback(oBugId, oProcessInformation, bIsMainProcess):
    asLog.append("%s process %d/0x%X (%s): attached." % (bIsMainProcess and "Main" or "Sub", \
        oProcessInformation.uId, oProcessInformation.uId, oProcessInformation.sBinaryName));
  def fProcessStartedCallback(oBugId, oConsoleProcess, bIsMainProcess):
    # This is always a main process
    asLog.append("%s process %d/0x%X (%s): started." % \
        (bIsMainProcess and "Main" or "Sub", oConsoleProcess.uId, oConsoleProcess.uId, oConsoleProcess.sBinaryName));
  def fProcessTerminatedCallback(oBugId, oProcessInformation, bIsMainProcess):
    asLog.append("%s process %d/0x%X (%s): terminated." % (bIsMainProcess and "Main" or "Sub", \
        oProcessInformation.uId, oProcessInformation.uId, oProcessInformation.sBinaryName));
  def fLogMessageCallback(oBugId, sMessage, dsData = None):
    sData = dsData and ", ".join(["%s: %s" % (sName, sValue) for (sName, sValue) in dsData.items()]);
    sLogLine = "log>%s%s" % (sMessage, sData and " (%s)" % sData or "");
    if gbShowCdbIO: fOutput(sLogLine);
    asLog.append(sLogLine);
  
  aoBugReports = [];
  def fBugReportCallback(oBugId, oBugReport):
    aoBugReports.append(oBugReport);
  
  if gbShowCdbIO:
    fOutput();
    fOutput("=" * 80);
    fOutput("%s %s" % (sApplicationBinaryPath, " ".join(asApplicationArguments)));
    if asExpectedBugIdAndLocations:
      for sExpectedBugIdAndLocation in asExpectedBugIdAndLocations:
        fOutput("  => %s" % sExpectedBugIdAndLocation);
    fOutput("-" * 80);
  bBugIdStarted = False;
  try:
    oBugId = cBugId(
      sCdbISA = sISA,
      sApplicationBinaryPath = sApplicationBinaryPath,
      asApplicationArguments = asApplicationArguments,
      asSymbolServerURLs = ["http://msdl.microsoft.com/download/symbols"], # Will be ignore if symbols are disabled.
      bGenerateReportHTML = gbGenerateReportHTML,
      uTotalMaxMemoryUse = guTotalMaxMemoryUse,
      uMaximumNumberOfBugs = uMaximumNumberOfBugs,
    );
    oBugId.fAddEventCallback("Application resumed", fApplicationResumedCallback);
    oBugId.fAddEventCallback("Application running", fApplicationRunningCallback);
    oBugId.fAddEventCallback("Application debug output", fApplicationDebugOutputCallback);
    oBugId.fAddEventCallback("Application stderr output", fApplicationStdErrOutputCallback);
    oBugId.fAddEventCallback("Application stdout output", fApplicationStdOutOutputCallback);
    oBugId.fAddEventCallback("Application suspended", fApplicationSuspendedCallback);
    oBugId.fAddEventCallback("Bug report", fBugReportCallback);
    oBugId.fAddEventCallback("Cdb stderr output", fCdbStdErrOutputCallback);
    oBugId.fAddEventCallback("Cdb stdin input", fCdbStdInInputCallback);
    oBugId.fAddEventCallback("Cdb stdout output", fCdbStdOutOutputCallback);
    oBugId.fAddEventCallback("Failed to apply application memory limits", fFailedToApplyMemoryLimitsCallback); 
    oBugId.fAddEventCallback("Failed to apply process memory limits", fFailedToApplyMemoryLimitsCallback); 
    oBugId.fAddEventCallback("Failed to debug application", fFailedToDebugApplicationCallback);
    oBugId.fAddEventCallback("Finished", fFinishedCallback);
    oBugId.fAddEventCallback("Internal exception", fInternalExceptionCallback);
    oBugId.fAddEventCallback("License warnings", fLicenseWarningsCallback);
    oBugId.fAddEventCallback("License errors", fLicenseErrorsCallback);
    oBugId.fAddEventCallback("Page heap not enabled", fPageHeapNotEnabledCallback);
    oBugId.fAddEventCallback("Process attached", fProcessAttachedCallback);
    oBugId.fAddEventCallback("Process terminated", fProcessTerminatedCallback);
    oBugId.fAddEventCallback("Process started", fProcessStartedCallback);
    oBugId.fAddEventCallback("Log message", fLogMessageCallback);
    if bExcessiveCPUUsageChecks:
      oBugId.fSetCheckForExcessiveCPUUsageTimeout(1);
    oBugId.fStart();
    bBugIdStarted = True;
    oBugId.fWait();
    if gbShowCdbIO: fOutput("= Finished ".ljust(80, "="));
    if gbTestFailed:
      return;
    def fDumpExpectedAndReported():
      uCounter = 0;
      while 1:
        sExpectedBugIdAndLocation = uCounter < len(asExpectedBugIdAndLocations) and asExpectedBugIdAndLocations[uCounter];
        oBugReport = uCounter < len(aoBugReports) and aoBugReports[uCounter];
        if not sExpectedBugIdAndLocation and not oBugReport:
          break;
        uCounter += 1;
        fOutput("  Expected #%d: %s" % (uCounter, sExpectedBugIdAndLocation));
        fOutput("  Reported   : %s" % (oBugReport and "%s @ %s" % (oBugReport.sId, oBugReport.sBugLocation)));
    if sExpectedFailedToDebugApplicationErrorMessage:
      pass;
    elif asExpectedBugIdAndLocations is None:
      uCounter = 0;
      for oBugReport in aoBugReports:
        uCounter += 1;
        sBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
        fOutput("* Test result for: %s" % sTestDescription);
        fOutput("  Test bug #%d: %s." % (uCounter, sBugIdAndLocation));
    elif asExpectedBugIdAndLocations:
      if len(aoBugReports) != len(asExpectedBugIdAndLocations):
        gbTestFailed = True;
        if not gbShowCdbIO: 
          for sLine in asLog:
            fOutput(sLine);
        fOutput("- Failed test: %s" % sTestDescription);
        fOutput("  Test reported %d instead of %d bugs in the application." % (len(aoBugReports), len(asExpectedBugIdAndLocations)));
        fDumpExpectedAndReported();
      else:
        uCounter = 0;
        for oBugReport in aoBugReports:
          sExpectedBugIdAndLocation = asExpectedBugIdAndLocations[uCounter];
          uCounter += 1;
          sBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
          if sExpectedBugIdAndLocation[0] == "*": # string contains a regular expression
            # Remove "*" and insert (escaped) test binary name in location
            sExpectedBugIdAndLocation = "^(%s)$" % sExpectedBugIdAndLocation[1:].replace("<test-binary>", re.escape(sTestBinaryName));
            bSuccess = re.match(sExpectedBugIdAndLocation, sBugIdAndLocation);
          else:
            sExpectedBugIdAndLocation = sExpectedBugIdAndLocation.replace("<test-binary>", sTestBinaryName);
            bSuccess = sBugIdAndLocation == sExpectedBugIdAndLocation;
          if not bSuccess:
            gbTestFailed = True;
            if not gbShowCdbIO: 
              for sLine in asLog:
                fOutput(sLine);
            fOutput("- Failed test: %s" % sTestDescription);
            fOutput("  Test bug #%d does not match %s." % (uCounter, sExpectedBugIdAndLocation));
            fDumpExpectedAndReported()
            break;
    if gbGenerateReportHTML:
      for oBugReport in aoBugReports:
        # We'd like a report file name base on the BugId, but the later may contain characters that are not valid in a file name
        sDesiredReportFileName = "%s %s @ %s.html" % (sPythonISA, oBugReport.sId, oBugReport.sBugLocation);
        # Thus, we need to translate these characters to create a valid filename that looks very similar to the BugId
        sValidReportFileName = mFileSystem.fsValidName(sDesiredReportFileName, bUnicode = False);
        sReportsFilePath = mFileSystem.fsPath(sReportsFolderName, sValidReportFileName);
        mFileSystem.fWriteDataToFile(
          oBugReport.sReportHTML,
          sReportsFilePath,
          fbRetryOnFailure = lambda: False,
        );
        fOutput("  Wrote report: %s" % sReportsFilePath);
  except Exception, oException:
    if bBugIdStarted:
      oBugId.fStop();
      oBugId.fWait();
    fOutput("- Failed test: %s" % sTestDescription);
    fOutput("  Exception:   %s" % repr(oException));
    raise;
  finally:
    if gbDebugStartFinish:
      fOutput("* Finished %s" % sTestDescription);

if __name__ == "__main__":
  asArgs = sys.argv[1:];
  bQuickTestSuite = False;
  bExtendedTestSuite = False;
  while asArgs:
    if asArgs[0] == "--all": 
      bExtendedTestSuite = True;
    elif asArgs[0] == "--report": 
      gbGenerateReportHTML = True;
    elif asArgs[0] == "--quick": 
      bQuickTestSuite = True;
    elif asArgs[0] == "--debug": 
      gbShowCdbIO = True;
    else:
      break;
    asArgs.pop(0);
  nStartTime = time.clock();
  if asArgs:
    gbShowApplicationIO = True;
    fOutput("* Starting test...");
    fTest(asArgs[0], asArgs[1:], None); # Expect no exceptions.
  else:
    fOutput("* Starting tests...");
    if not bExtendedTestSuite:
      # When we're not running the full test suite, we're not saving reports, so we don't need symbols.
      # Disabling symbols should speed things up considerably.
      cBugId.dxConfig["asDefaultSymbolServerURLs"] = None;
    # This will try to debug a non-existing application and check that the error thrown matches the expected value.
    fTest("x86",     None,                                                      [], \
        sApplicationBinaryPath = "<invalid>", \
        sExpectedFailedToDebugApplicationErrorMessage = "Unable to start a new process for binary \"<invalid>\".");
    fTest("x86",     None,                                                      [], \
        sApplicationBinaryPath = "does not exist", \
        sExpectedFailedToDebugApplicationErrorMessage = "Unable to start a new process for binary \"does not exist\".");
    for sISA in asTestISAs:
      fTest(sISA,    ["Nop"],                                                   []); # No exceptions, just a clean program exit.
      fTest(sISA,    ["Breakpoint"],                                            ["Breakpoint ed2.531 @ <test-binary>!wmain"]);
      if bQuickTestSuite:
        continue; # Just do a test without a crash and breakpoint.
      # This will run the test in a cmd shell, so the exception happens in a child process. This should not affect the outcome.
      fTest(sISA,    ["Breakpoint"],                                            ["Breakpoint ed2.531 @ <test-binary>!wmain"],
          bRunInShell = True);
      fTest(sISA,    ["CPUUsage"],                                              ["CPUUsage ed2.531 @ <test-binary>!wmain"],
          bExcessiveCPUUsageChecks = True);
      fTest(sISA,    ["C++"],                                                   ["C++:cException ed2.531 @ <test-binary>!wmain"]);
      fTest(sISA,    ["IntegerDivideByZero"],                                   ["IntegerDivideByZero ed2.531 @ <test-binary>!wmain"]);
# This test will throw a first chance integer overflow, but Visual Studio added an exception Callback that then triggers
# another exception, so the report is incorrect.
#      fTest(sISA,    ["IntegerOverflow"],                                      "IntegerOverflow xxx.ed2");
      fTest(sISA,    ["Numbered", 0x41414141, 0x42424242],                      ["0x41414141 ed2.531 @ <test-binary>!wmain"]);
      fTest(sISA,    ["IllegalInstruction"],                                    ["*IllegalInstruction f17\.(f17|ed2) @ <test-binary>!fIllegalInstruction"]);
      fTest(sISA,    ["PrivilegedInstruction"],                                 ["*PrivilegedInstruction 0fc\.(0fc|ed2) @ <test-binary>!fPrivilegedInstruction"]);
      fTest(sISA,    ["StackExhaustion", 0x100],                                ["StackExhaustion ed2.531 @ <test-binary>!wmain"]);
      fTest(sISA,    ["RecursiveCall", 2],                                      ["RecursiveCall 950.6d1 @ <test-binary>!fStackRecursionFunction1"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["RecursiveCall", 1],                                      ["RecursiveCall 950 @ <test-binary>!fStackRecursionFunction1"]);
        fTest(sISA,  ["RecursiveCall", 3],                                      ["RecursiveCall 950.4e9 @ <test-binary>!fStackRecursionFunction1"]);
        fTest(sISA,  ["RecursiveCall", 20],                                     ["RecursiveCall 950.48b @ <test-binary>!fStackRecursionFunction1"]);
      # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
      # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
      # depends on the build of the application and whether symbols are being used.
      fTest(sISA,    ["PureCall"],                                              ["PureCall 12d.838 @ <test-binary>!fCallVirtual"]);
      fTest(sISA,    ["WrongHeapHandle", 0x20],                                 ["WrongHeap[4n] ed2.531 @ <test-binary>!wmain"]);
      fTest(sISA,    ["OOM", "HeapAlloc", guOOMAllocationBlockSize],            ["OOM ed2.531 @ <test-binary>!wmain"]);
      fTest(sISA,    ["OOM", "C++", guOOMAllocationBlockSize],                  ["OOM ed2.531 @ <test-binary>!wmain"]);
      fTest(sISA,    ["OOM", "Stack", guOOMAllocationBlockSize],                ["OOM ed2.531 @ <test-binary>!wmain"]);
      # WRT
      fTest(sISA,    ["WRTOriginate", 0x87654321, "message"],                   ["Stowed[0x87654321] ed2.531 @ <test-binary>!wmain"]);
      fTest(sISA,    ["WRTLanguage",  0x87654321, "message"],                   ["Stowed[0x87654321:WRTLanguage@cIUnknown] ed2.531 @ <test-binary>!wmain"]);
      # Double free
      fTest(sISA,    ["DoubleFree",                1],                          ["DoubleFree[1] ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["DoubleFree",                2],                          ["DoubleFree[2] ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["DoubleFree",                3],                          ["DoubleFree[3] ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["DoubleFree",                4],                          ["DoubleFree[4n] ed2.531 @ <test-binary>!wmain"]);
        # Extra tests to check if the code deals correctly with memory areas too large to dump completely:
        uMax = cBugId.dxConfig["uMaxMemoryDumpSize"];
        fTest(sISA,  ["DoubleFree",             uMax],                          ["DoubleFree[4n] ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["DoubleFree",         uMax + 1],                          ["DoubleFree[4n+1] ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["DoubleFree",         uMax + 4],                          ["DoubleFree[4n] ed2.531 @ <test-binary>!wmain"]);
        
      # Misaligned free
      fTest(sISA,    ["MisalignedFree",            1,  1],                      ["MisalignedFree[1]+0 ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["MisalignedFree",            1,  2],                      ["MisalignedFree[1]+1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            2,  4],                      ["MisalignedFree[2]+2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            3,  6],                      ["MisalignedFree[3]+3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            4,  8],                      ["MisalignedFree[4n]+4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            5,  10],                     ["MisalignedFree[4n+1]+4n+1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            2,  1],                      ["MisalignedFree[2]@1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            3,  2],                      ["MisalignedFree[3]@2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            4,  3],                      ["MisalignedFree[4n]@3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            5,  4],                      ["MisalignedFree[4n+1]@4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            1,  -1],                     ["MisalignedFree[1]-1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            1,  -2],                     ["MisalignedFree[1]-2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            1,  -3],                     ["MisalignedFree[1]-3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            1,  -4],                     ["MisalignedFree[1]-4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["MisalignedFree",            1,  -5],                     ["MisalignedFree[1]-4n-1 ed2.531 @ <test-binary>!wmain"]);
      # NULL pointers
      fTest(sISA,    ["AccessViolation",   "Read",     1],                      ["AVR@NULL+1 ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["AccessViolation",   "Read", 2],                          ["AVR@NULL+2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", 3],                          ["AVR@NULL+3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", 4],                          ["AVR@NULL+4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", 5],                          ["AVR@NULL+4n+1 ed2.531 @ <test-binary>!wmain"]);
      uSignPadding = {"x86": 0, "x64": 0xFFFFFFFF00000000}[sISA];
      fTest(sISA,    ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFF],    ["AVR@NULL-1 ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFE],    ["AVR@NULL-2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFD],    ["AVR@NULL-3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFC],    ["AVR@NULL-4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFB],    ["AVR@NULL-4n-1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFA],    ["AVR@NULL-4n-2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF9],    ["AVR@NULL-4n-3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF8],    ["AVR@NULL-4n ed2.531 @ <test-binary>!wmain"]);
      # These are detected by Page Heap / Application Verifier
      fTest(sISA,    ["OutOfBounds", "Heap", "Write", 1, -1, 1],                ["OOBW[1]{-1~1} ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["OutOfBounds", "Heap", "Write", 2, -2, 2],                ["OOBW[2]{-2~2} ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["OutOfBounds", "Heap", "Write", 3, -3, 3],                ["OOBW[3]{-3~3} ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["OutOfBounds", "Heap", "Write", 4, -4, 4],                ["OOBW[4n]{-4n~4n} ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["OutOfBounds", "Heap", "Write", 5, -5, 5],                ["OOBW[4n+1]{-4n-1~4n+1} ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["OutOfBounds", "Heap", "Write", 1, -4, 5],                ["OOBW[1]{-4n~4n} ed2.531 @ <test-binary>!wmain"]); # Last byte written is within bounds!
        # Make sure very large allocations do not cause issues in cBugId
        fTest(sISA,  ["OutOfBounds", "Heap", "Write", guLargeHeapBlockSize, -4, 4], ["OOBW[4n]{-4n~4n} ed2.531 @ <test-binary>!wmain"]);
      # Page heap does not appear to work for x86 tests on x64 platform.
      fTest(sISA,    ["UseAfterFree", "Read",    1,  0],                        ["RAF[1]@0 ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["UseAfterFree", "Write",   2,  1],                        ["WAF[2]@1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Read",    3,  2],                        ["RAF[3]@2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Write",   4,  3],                        ["WAF[4n]@3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Read",    5,  4],                        ["RAF[4n+1]@4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Write",   6,  5],                        ["WAF[4n+2]@4n+1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Call",    8,  0],                        ["EAF[4n]@0 f47.ed2 @ <test-binary>!fCall"]);
        fTest(sISA,  ["UseAfterFree", "Jump",    8,  0],                        ["EAF[4n]@0 46f.ed2 @ <test-binary>!fJump"]);
      fTest(sISA,    ["UseAfterFree", "Read",    1,  1],                        ["OOBRAF[1]+0 ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["UseAfterFree", "Write",   2,  3],                        ["OOBWAF[2]+1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Read",    3,  5],                        ["OOBRAF[3]+2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Write",   4,  7],                        ["OOBWAF[4n]+3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Read",    5,  9],                        ["OOBRAF[4n+1]+4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Write",   6, 11],                        ["OOBWAF[4n+2]+4n+1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Read",    1, -1],                        ["OOBRAF[1]-1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Write",   1, -2],                        ["OOBWAF[1]-2 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Read",    1, -3],                        ["OOBRAF[1]-3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Write",   1, -4],                        ["OOBWAF[1]-4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Read",    1, -5],                        ["OOBRAF[1]-4n-1 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["UseAfterFree", "Call",    8,  8],                        ["OOBEAF[4n]+0 f47.ed2 @ <test-binary>!fCall"]);
        fTest(sISA,  ["UseAfterFree", "Jump",    8,  8],                        ["OOBEAF[4n]+0 46f.ed2 @ <test-binary>!fJump"]);
      # These issues are not detected until they cause an access violation. Heap blocks may be aligned up to 0x10 bytes.
      fTest(sISA,    ["BufferOverrun",   "Heap", "Read",   0xC, 5],             ["OOBR[4n]+4n ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        fTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xD, 5],             ["OOBR[4n+1]+3 ed2.531 @ <test-binary>!wmain", "OOBR[4n+1]+4n ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xE, 5],             ["OOBR[4n+2]+2 ed2.531 @ <test-binary>!wmain", "OOBR[4n+2]+3 ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xF, 5],             ["OOBR[4n+3]+1 ed2.531 @ <test-binary>!wmain", "OOBR[4n+3]+2 ed2.531 @ <test-binary>!wmain"]);
      # These issues are detected when they cause an access violation, but earlier OOBWs took place that did not cause AVs.
      # This causes memory corruption, which is detected and reportd in the bug id between curly braces.
      # This next test causes one AV, which is reported first. Then when collateral continues and the application
      # frees the memory, verifier.dll notices the corruption and reports it as well...
      fTest(sISA,    ["BufferOverrun",   "Heap", "Write",  0xC, 5],             ["BOF[4n]+4n{+0~4n} ed2.531 @ <test-binary>!wmain", "BOF[4n]{+0~4n} ed2.531 @ <test-binary>!wmain"]);
      if bExtendedTestSuite:
        # These tests cause multiple AVs as the buffer overflow continues to write beyond the end of the buffer.
        # The first one is detect as a BOF, as the AV is sequential to the heap corruption in the heap block suffix.
        # The second AV is sequential to the first, but no longer to the heap corruption, so it is not detected as a BOF
        fTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xD, 5],             ["BOF[4n+1]+3{+0~3} ed2.531 @ <test-binary>!wmain", "OOBW[4n+1]+4n{+0~3} ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xE, 5],             ["BOF[4n+2]+2{+0~2} ed2.531 @ <test-binary>!wmain", "OOBW[4n+2]+3{+0~2} ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xF, 5],             ["BOF[4n+3]+1{+0~1} ed2.531 @ <test-binary>!wmain", "OOBW[4n+3]+2{+0~1} ed2.531 @ <test-binary>!wmain"]);
        # For this buffer overflow, there is no heap block suffix in which to detect corruption, so it cannot be
        # detected as a BOF.
        fTest(sISA,  ["BufferOverrun",   "Heap", "Write", 0x10, 5],             ["OOBW[4n]+0 ed2.531 @ <test-binary>!wmain", "OOBW[4n]+1 ed2.531 @ <test-binary>!wmain"]); # First byte writen causes AV; no data hash
      # Stack based heap overflows can cause an access violation if the run off the end of the stack, or a debugbreak
      # when they overwrite the stack cookie and the function returns. Finding out how much to write to overwrite the
      # stack cookie but not run off the end of the stack requires a bit of dark magic. I've only tested these values
      # on x64!
      uSmash = sISA == "x64" and 0x200 or 0x100;
      fTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, uSmash],        ["OOBW@Stack ed2.531 @ <test-binary>!wmain"]);
      # The OS does not allocate a guard page at the top of the stack. Subsequently, there may be a writable allocation
      # there, and a large enough stack overflow will write way past the end of the stack before causing an AV. This
      # causes a different BugId, so this test is not reliable at the moment.
      # TODO: Reimplement pagehap and add feature that adds guard pages to all virtual allocations, so stacks buffer
      # overflows are detected as soon as they read/write past the end of the stack.
      # fTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, 0x100000],     "AVW[Stack]+0 ed2.531 @ <test-binary>!wmain");
      
      if bExtendedTestSuite:
        for (uBaseAddress, sDescription) in [
          # 0123456789ABCDEF
                 (0x44444444, "Unallocated"), # This is not guaranteed, but in my experience it's reliable.
             (0x7ffffffdffff, "Unallocated"), # Highly unlikely to be allocated as it is at the very top of allocatable mem.
             (0x7ffffffe0000, "Reserved"),
             (0x7ffffffeffff, "Reserved"),
             (0x7fffffff0000, "Invalid"),
             (0x7fffffffffff, "Invalid"),
             (0x800000000000, "Invalid"),
         (0x8000000000000000, "Invalid"),
        ]:
          if uBaseAddress < (1 << 32) or sISA == "x64":
            # On x64, there are some limitations to exceptions occuring at addresses between the userland and kernelland
            # memory address ranges.
            fTest(sISA,  ["AccessViolation", "Read", uBaseAddress],             ["AVR@%s ed2.531 @ <test-binary>!wmain" % sDescription]);
            if uBaseAddress >= 0x800000000000 and uBaseAddress < 0xffff800000000000:
              fTest(sISA,  ["AccessViolation", "Write", uBaseAddress],          ["AV?@%s ed2.531 @ <test-binary>!wmain" % sDescription]);
              fTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],           ["AVE@%s 46f.ed2 @ <test-binary>!fJump" % sDescription]);
            else:
              fTest(sISA,  ["AccessViolation", "Write", uBaseAddress],          ["AVW@%s ed2.531 @ <test-binary>!wmain" % sDescription]);
              fTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],           ["AVE@%s 46f.ed2 @ <test-binary>!fJump" % sDescription]);
            fTest(sISA,    ["AccessViolation", "Call", uBaseAddress],           ["AVE@%s f47.ed2 @ <test-binary>!fCall" % sDescription]);
        
        for (uBaseAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in gddtsDetails_uSpecialAddress_sISA[sISA].items():
          if uBaseAddress < (1 << 32) or (sISA == "x64" and uBaseAddress < (1 << 47)):
            fTest(sISA,    ["AccessViolation", "Read", uBaseAddress],           ["AVR@%s ed2.531 @ <test-binary>!wmain" % sAddressId]);
            if bExtendedTestSuite:
              fTest(sISA,  ["AccessViolation", "Write", uBaseAddress],          ["AVW@%s ed2.531 @ <test-binary>!wmain" % sAddressId]);
              fTest(sISA,  ["AccessViolation", "Call", uBaseAddress],           ["AVE@%s f47.ed2 @ <test-binary>!fCall" % sAddressId]);
              fTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],           ["AVE@%s 46f.ed2 @ <test-binary>!fJump" % sAddressId]);
          elif sISA == "x64":
            fTest(sISA,    ["AccessViolation", "Read", uBaseAddress],           ["AVR@%s ed2.531 @ <test-binary>!wmain" % sAddressId]);
            if bExtendedTestSuite:
              fTest(sISA,  ["AccessViolation", "Write", uBaseAddress],          ["AV?@%s ed2.531 @ <test-binary>!wmain" % sAddressId]);
              fTest(sISA,  ["AccessViolation", "Call", uBaseAddress],           ["AVE@%s f47.ed2 @ <test-binary>!fCall" % sAddressId]);
              fTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],           ["AVE@%s 46f.ed2 @ <test-binary>!fJump" % sAddressId]);
      # SafeInt tests
      if not bExtendedTestSuite:
        fTest(sISA,    ["SafeInt", "++", "signed", 64],                         ["IntegerOverflow ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,    ["SafeInt", "--", "unsigned", 32],                       ["IntegerOverflow ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,    ["SafeInt", "*",  "signed", 16],                         ["IntegerOverflow ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,    ["SafeInt", "truncate",  "signed", 8],                   ["IntegerTruncation ed2.531 @ <test-binary>!wmain"]);
        fTest(sISA,    ["SafeInt", "signedness",  "signed", 16],                ["IntegerTruncation ed2.531 @ <test-binary>!wmain"]);
      else:
        for (sOperation, sTypeId) in {
          "++": "IntegerOverflow",
          "--": "IntegerOverflow",
          "*": "IntegerOverflow",
          "truncate": "IntegerTruncation",
          "signedness": "IntegerTruncation",
        }.items():
          for sSignedness in ["signed", "unsigned"]:
            for uBits in [8, 16, 32, 64]:
              if uBits != 64 and sOperation != "truncate":
                fTest(sISA,    ["SafeInt", sOperation, sSignedness, uBits],     ["%s ed2.531 @ <test-binary>!wmain" % sTypeId]);
  nTestTime = time.clock() - nStartTime;
  if gbTestFailed:
    fOutput("- Testing failed after %3.3f seconds" % nTestTime);
    sys.exit(1);
  else:
    fOutput("+ Testing completed in %3.3f seconds" % nTestTime);
    sys.exit(0);
