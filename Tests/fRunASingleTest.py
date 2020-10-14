import os, re, traceback;
from cBugId import cBugId;
from oConsole import oConsole;
import mGlobals;

try:
  import mDebugOutput;
except:
  mDebugOutput = None;

ERROR = 0x0F0C;
WARN = 0x0F0E;

mGlobals.bLicenseWarningsShown = False;


def fRunASingleTest(
  sISA,
  axCommandLineArguments,
  asExpectedBugIdAndLocations,
  sExpectedFailedToDebugApplicationErrorMessage = None,
  bRunInShell = False,
  sApplicationBinaryPath = None,
  uMaximumNumberOfBugs = 2,
  bExcessiveCPUUsageChecks = False
):
  asApplicationArguments = axCommandLineArguments and [
    isinstance(x, str) and x
             or x < 10 and ("%d" % x)
                        or ("0x%X" % x)
    for x in axCommandLineArguments
  ] or [];
  if sApplicationBinaryPath is None:
    sApplicationBinaryPath = mGlobals.dsTestsBinaries_by_sISA[sISA];
  asCommandLine = [sApplicationBinaryPath] + asApplicationArguments;
  sFailedToDebugApplicationErrorMessage = None;
  if sExpectedFailedToDebugApplicationErrorMessage:
    sTestDescription = "%s => %s" % (
      "Running %s" % sApplicationBinaryPath,
      repr(sExpectedFailedToDebugApplicationErrorMessage)
    );
  else:
    sTestDescription = "%s %s%s => %s" % (
      sISA,
      " ".join(asApplicationArguments), \
      bRunInShell and " (in child process)" or "",
      asExpectedBugIdAndLocations and " => ".join(asExpectedBugIdAndLocations) or "no bugs"
    );
  
  sTestBinaryName = os.path.basename(sApplicationBinaryPath).lower();
  
  if bRunInShell:
    asApplicationArguments = ["/C", sApplicationBinaryPath] + asApplicationArguments; 
    sApplicationBinaryPath = mGlobals.dsComSpec_by_sISA[sISA];
  
  oConsole.fSetTitle(sTestDescription);
  if mGlobals.bDebugStartFinish:
    oConsole.fOutput("* Started %s" % sTestDescription);
  else:
    oConsole.fStatus("* %s" % sTestDescription);
  
  asLog = [];
  def fCdbStdInInputCallback(oBugId, sInput):
    if mGlobals.bShowCdbIO: oConsole.fOutput("stdin<%s" % sInput);
    asLog.append("stdin<%s" % sInput);
  def fCdbStdOutOutputCallback(oBugId, sOutput):
    if mGlobals.bShowCdbIO: oConsole.fOutput("stdout>%s" % sOutput);
    asLog.append("stdout>%s" % sOutput);
  def fCdbStdErrOutputCallback(oBugId, sOutput):
    if mGlobals.bShowCdbIO: oConsole.fOutput("stderr>%s" % sOutput);
    asLog.append("stderr>%s" % sOutput);
#    asLog.append("log>%s%s" % (sMessage, sData and " (%s)" % sData or ""));
  def fApplicationDebugOutputCallback(oBugId, oProcess, bIsMainProcess, asOutput):
    bFirstLine = True;
    for sOutput in asOutput:
      sLogLine = "%s process 0x%X (%s): %s>%s" % (
        bIsMainProcess and "Main" or "Sub", \
        oProcess.uId,
        oProcess.sCommandLine,
        bFirstLine and "debug" or "     ",
        sOutput
      );
      if mGlobals.bShowApplicationIO: oConsole.fOutput(sLogLine);
      asLog.append(sLogLine);
      bFirstLine = False;
  def fApplicationStdErrOutputCallback(oBugId, oConsoleProcess, bIsMainProcess, sOutput):
    # This is always a main process
    sLogLine = "%s process 0x%X (%s): stderr> %s" % (
      bIsMainProcess and "Main" or "Sub",
      oConsoleProcess.uId,
      oConsoleProcess.sCommandLine,
      sOutput
    );
    if mGlobals.bShowApplicationIO: oConsole.fOutput(sLogLine);
    asLog.append(sLogLine);
  def fApplicationStdOutOutputCallback(oBugId, oConsoleProcess, bIsMainProcess, sOutput):
    # This is always a main process
    sLogLine = "%s process 0x%X (%s): stdout> %s" % (
      bIsMainProcess and "Main" or "Sub",
      oConsoleProcess.uId,
      oConsoleProcess.sCommandLine,
      sOutput
    )
    if mGlobals.bShowApplicationIO: oConsole.fOutput(sLogLine);
    asLog.append(sLogLine);
  def fApplicationSuspendedCallback(oBugId, sReason):
    asLog.append("Application suspended (%s)" % sReason);
  def fApplicationResumedCallback(oBugId):
    asLog.append("Application resumed");
  def fApplicationRunningCallback(oBugId):
    asLog.append("Application running");
  def fFailedToDebugApplicationCallback(oBugId, sErrorMessage):
    if sExpectedFailedToDebugApplicationErrorMessage == sErrorMessage:
      return;
    if not mGlobals.bShowCdbIO: 
      for sLine in asLog:
        oConsole.fOutput(sLine);
    oConsole.fOutput(ERROR, "- Failed test: %s" % sTestDescription);
    if sExpectedFailedToDebugApplicationErrorMessage:
      oConsole.fOutput(ERROR, "  Expected:    %s" % repr(sExpectedFailedToDebugApplicationErrorMessage));
    else:
      oConsole.fOutput(ERROR, "  BugId unexpectedly failed to debug the application");
    oConsole.fOutput(ERROR, "  Error:       %s" % repr(sErrorMessage));
    oBugId.fStop();
    raise AssertionError(sErrorMessage);
  def fFailedToApplyMemoryLimitsCallback(oBugId, oProcess):
    if not mGlobals.bShowCdbIO: 
      for sLine in asLog:
        oConsole.fOutput(ERROR, sLine);
    oConsole.fOutput(ERROR, "- Failed to apply memory limits to process 0x%X (%s) for test: %s" % (
      oProcess.uId,
      oProcess.sCommandLine,
      sTestDescription
    ));
    oBugId.fStop();
    raise AssertionError("Failed to apply memory limits to process");
  def fFinishedCallback(oBugId):
    if mGlobals.bShowCdbIO: oConsole.fOutput("Finished");
    asLog.append("Finished");
  def fLicenseWarningsCallback(oBugId, asLicenseWarnings):
    if not mGlobals.bLicenseWarningsShown:
      oConsole.fOutput(WARN, "@" * 80);
      for sLicenseWarning in asLicenseWarnings:
        oConsole.fOutput(WARN, "@ %s" % sLicenseWarning);
      oConsole.fOutput(WARN, "@" * 80);
      mGlobals.bLicenseWarningsShown = True;
  def fLicenseErrorsCallback(oBugId, asLicenseErrors):
    oConsole.fOutput(ERROR, "@" * 80);
    for sLicenseError in asLicenseErrors:
      oConsole.fOutput(ERROR, "@ %s" % sLicenseError);
    oConsole.fOutput(ERROR, "@" * 80);
    os._exit(1);
  
  def fInternalExceptionCallback(oBugId, oThread, oException, oTraceBack):
    if not mGlobals.bShowCdbIO: 
      for sLine in asLog:
        oConsole.fOutput(sLine);
    oBugId.fStop();
    if mDebugOutput:
      mDebugOutput.fTerminateWithException(oException, oTraceBack, bShowStacksForAllThread = True);
  def fPageHeapNotEnabledCallback(oBugId, oProcess, bIsMainProcess, bPreventable):
    assert oProcess.sBinaryName == "cmd.exe", \
        "It appears you have not enabled page heap for %s, which is required to run tests." % oProcess.sBinaryName;
  def fProcessAttachedCallback(oBugId, oProcess, bIsMainProcess):
    asLog.append("%s process 0x%X (%s): attached." % (
      bIsMainProcess and "Main" or "Sub",
      oProcess.uId,
      oProcess.sCommandLine
    ));
  def fProcessStartedCallback(oBugId, oConsoleProcess, bIsMainProcess):
    # This is always a main process
    asLog.append("%s process 0x%X (%s): started." % (
      bIsMainProcess and "Main" or "Sub",
      oConsoleProcess.uId,
      oConsoleProcess.sCommandLine
    ));
  def fProcessTerminatedCallback(oBugId, oProcess, bIsMainProcess):
    asLog.append("%s process 0x%X (%s): terminated." % (
      bIsMainProcess and "Main" or "Sub",
      oProcess.uId,
      oProcess.sCommandLine
    ));
  def fLogMessageCallback(oBugId, sMessage, dsData = None):
    sData = dsData and ", ".join(["%s: %s" % (sName, sValue) for (sName, sValue) in dsData.items()]);
    sLogLine = "log>%s%s" % (sMessage, sData and " (%s)" % sData or "");
    if mGlobals.bShowCdbIO: oConsole.fOutput(sLogLine);
    asLog.append(sLogLine);
  
  aoBugReports = [];
  def fBugReportCallback(oBugId, oBugReport):
    aoBugReports.append(oBugReport);
  
  if mGlobals.bShowCdbIO:
    oConsole.fOutput();
    oConsole.fOutput("=" * 80);
    oConsole.fOutput("%s %s" % (sApplicationBinaryPath, " ".join(asApplicationArguments)));
    if asExpectedBugIdAndLocations:
      for sExpectedBugIdAndLocation in asExpectedBugIdAndLocations:
        oConsole.fOutput("  => %s" % sExpectedBugIdAndLocation);
    oConsole.fOutput("-" * 80);
  bBugIdStarted = False;
  bBugIdStopped = False;
  try:
    oBugId = cBugId(
      sCdbISA = sISA, # Debug with a cdb.exe for an ISA that matches the target process.
      sApplicationBinaryPath = sApplicationBinaryPath,
      asApplicationArguments = asApplicationArguments,
      asSymbolServerURLs = ["http://msdl.microsoft.com/download/symbols"], # Will be ignore if symbols are disabled.
      bGenerateReportHTML = mGlobals.bGenerateReportHTML,
      uTotalMaxMemoryUse = mGlobals.uTotalMaxMemoryUse,
      uMaximumNumberOfBugs = uMaximumNumberOfBugs,
    );
    oBugId.fAddCallback("Application resumed", fApplicationResumedCallback);
    oBugId.fAddCallback("Application running", fApplicationRunningCallback);
    oBugId.fAddCallback("Application debug output", fApplicationDebugOutputCallback);
    oBugId.fAddCallback("Application stderr output", fApplicationStdErrOutputCallback);
    oBugId.fAddCallback("Application stdout output", fApplicationStdOutOutputCallback);
    oBugId.fAddCallback("Application suspended", fApplicationSuspendedCallback);
    oBugId.fAddCallback("Bug report", fBugReportCallback);
    oBugId.fAddCallback("Cdb stderr output", fCdbStdErrOutputCallback);
    oBugId.fAddCallback("Cdb stdin input", fCdbStdInInputCallback);
    oBugId.fAddCallback("Cdb stdout output", fCdbStdOutOutputCallback);
    oBugId.fAddCallback("Failed to apply application memory limits", fFailedToApplyMemoryLimitsCallback); 
    oBugId.fAddCallback("Failed to apply process memory limits", fFailedToApplyMemoryLimitsCallback); 
    oBugId.fAddCallback("Failed to debug application", fFailedToDebugApplicationCallback);
    oBugId.fAddCallback("Finished", fFinishedCallback);
    oBugId.fAddCallback("Internal exception", fInternalExceptionCallback);
    oBugId.fAddCallback("License warnings", fLicenseWarningsCallback);
    oBugId.fAddCallback("License errors", fLicenseErrorsCallback);
    oBugId.fAddCallback("Page heap not enabled", fPageHeapNotEnabledCallback);
    oBugId.fAddCallback("Process attached", fProcessAttachedCallback);
    oBugId.fAddCallback("Process terminated", fProcessTerminatedCallback);
    oBugId.fAddCallback("Process started", fProcessStartedCallback);
    oBugId.fAddCallback("Log message", fLogMessageCallback);
    if bExcessiveCPUUsageChecks:
      def fExcessiveCPUUsageDetectedCallback(oBugId, bExcessiveCPUUsageDetected):
        if not bExcessiveCPUUsageDetected:
          oBugId.fCheckForExcessiveCPUUsage(fExcessiveCPUUsageDetectedCallback);
      oBugId.foSetTimeout(
        sDescription = "Start check for excessive CPU usage",
        nTimeoutInSeconds = mGlobals.nExcessiveCPUUsageCheckInitialTimeoutInSeconds,
        f0Callback = lambda oBugId: fExcessiveCPUUsageDetectedCallback(oBugId, False),
      );
    oBugId.fStart();
    bBugIdStarted = True;
    oBugId.fWait();
    bBugIdStopped = True;
    if mGlobals.bShowCdbIO: oConsole.fOutput("= Finished ".ljust(80, "="));
    def fDumpExpectedAndReported():
      uCounter = 0;
      while 1:
        sExpectedBugIdAndLocation = uCounter < len(asExpectedBugIdAndLocations) and asExpectedBugIdAndLocations[uCounter];
        oBugReport = uCounter < len(aoBugReports) and aoBugReports[uCounter];
        if not sExpectedBugIdAndLocation and not oBugReport:
          break;
        uCounter += 1;
        oConsole.fOutput("  Expected #%d: %s" % (uCounter, sExpectedBugIdAndLocation));
        oConsole.fOutput("  Reported   : %s" % (oBugReport and "%s @ %s" % (oBugReport.sId, oBugReport.sBugLocation)));
        if oBugReport:
          oConsole.fOutput("               %s" % oBugReport.sBugDescription);
    if sExpectedFailedToDebugApplicationErrorMessage:
      pass;
    elif asExpectedBugIdAndLocations is None:
      uCounter = 0;
      for oBugReport in aoBugReports:
        uCounter += 1;
        sBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
        oConsole.fOutput("* Test result for: %s" % sTestDescription);
        oConsole.fOutput("  Test bug #%d: %s." % (uCounter, sBugIdAndLocation));
    elif asExpectedBugIdAndLocations:
      if len(aoBugReports) != len(asExpectedBugIdAndLocations):
        if not mGlobals.bShowCdbIO: 
          for sLine in asLog:
            oConsole.fOutput(sLine);
        oConsole.fOutput(ERROR, "- Failed test: %s" % sTestDescription);
        oConsole.fOutput(ERROR, "  Test reported %d instead of %d bugs in the application." % (len(aoBugReports), len(asExpectedBugIdAndLocations)));
        fDumpExpectedAndReported();
        raise AssertionError("Test reported different number of bugs than was expected");
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
            if not mGlobals.bShowCdbIO: 
              for sLine in asLog:
                oConsole.fOutput(ERROR, sLine);
            oConsole.fOutput(ERROR, "- Failed test: %s" % sTestDescription);
            oConsole.fOutput(ERROR, "  Test bug #%d does not match %s." % (uCounter, sExpectedBugIdAndLocation));
            fDumpExpectedAndReported()
            raise AssertionError("Test reported unexpected Bug Id and/or Location.");
    if mGlobals.bSaveReportHTML:
      for oBugReport in aoBugReports:
        # We'd like a report file name base on the BugId, but the later may contain characters that are not valid in a file name
        sDesiredReportFileName = "%s %s @ %s.html" % (sPythonISA, oBugReport.sId, oBugReport.sBugLocation);
        # Thus, we need to translate these characters to create a valid filename that looks very similar to the BugId
        sValidReportFileName = mFileSystem2.fsGetValidName(sDesiredReportFileName, bUnicode = False);
        sReportsFilePath = os.path.join(mGlobals.sReportsFolderPath, sValidReportFileName);
        mFileSystem2.foCreateFile(sReportsFilePath, oBugReport.sReportHTML);
        oConsole.fOutput("  Wrote report: %s" % sReportsFilePath);
  except Exception, oException:
    if bBugIdStarted and not bBugIdStopped:
      oBugId.fTerminate();
    oConsole.fOutput(ERROR, "- Failed test: %s" % sTestDescription);
    oConsole.fOutput(ERROR, "  Exception:   %s" % repr(oException));
    raise;
  finally:
    if mGlobals.bDebugStartFinish:
      oConsole.fOutput("* Finished %s" % sTestDescription);