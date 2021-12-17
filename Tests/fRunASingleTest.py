import os, re, traceback;
from mBugId import cBugId;
from mConsole import oConsole;
from mFileSystemItem import cFileSystemItem;
import mGlobals;
from mBugId.mCP437 import fsCP437FromBytesString;

try: # mDebugOutput use is Optional
  import mDebugOutput as m0DebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  m0DebugOutput = None;

NORMAL = 0x0F07;
HILITE = 0x0F0F;
ERROR = 0x0F0C;
WARN = 0x0F06;
WARN_INFO = 0x0F0E;

mGlobals.bLicenseWarningsShown = False;

def fOutputStack(oStack):
  oConsole.fOutput(HILITE, "  Stack:");
  for oStackFrame in oStack.aoFrames:
    oConsole.fOutput(
      NORMAL, "  \u2022 ",
      NORMAL if oStackFrame.bHidden else HILITE, fsCP437FromBytesString(oStackFrame.sb0UniqueAddress or b"---"),
      NORMAL, " (cdb:", NORMAL if oStackFrame.sb0UniqueAddress else HILITE, fsCP437FromBytesString(oStackFrame.sbCdbSymbolOrAddress), NORMAL, ")",
      [" => ", oStackFrame.s0IsHiddenBecause] if oStackFrame.s0IsHiddenBecause else [], 
    );

guExitCodeInternalError = 1; # Use standard value;
def fRunASingleTest(
  sISA,
  axCommandLineArguments,
  a0sExpectedBugIdAndLocations,
  sExpectedFailedToDebugApplicationErrorMessage = None,
  bRunInShell = False,
  s0ApplicationBinaryPath = None,
  bASan = False,
  uMaximumNumberOfBugs = 2,
  bExcessiveCPUUsageChecks = False
):
  asApplicationArguments = axCommandLineArguments and [
    isinstance(x, str) and x
             or x < 10 and ("%d" % x)
                        or ("0x%X" % x)
    for x in axCommandLineArguments
  ] or [];
  assert s0ApplicationBinaryPath is None or not bASan, \
      "Setting bASan when supplying an application binary path makes no sense";
  sApplicationBinaryPath = (
    s0ApplicationBinaryPath if s0ApplicationBinaryPath is not None else 
    mGlobals.dsASanTestsBinaries_by_sISA[sISA] if bASan else
    mGlobals.dsTestsBinaries_by_sISA[sISA]
  );
  asCommandLine = [sApplicationBinaryPath] + asApplicationArguments;
  sFailedToDebugApplicationErrorMessage = None;
  if sExpectedFailedToDebugApplicationErrorMessage:
    sTestDescription = "%s => %s" % (
      "Running %s" % sApplicationBinaryPath,
      repr(sExpectedFailedToDebugApplicationErrorMessage)
    );
  else:
    sTestDescription = "%s%s %s%s => %s" % (
      sISA,
      " ASan" if bASan else "",
      " ".join(asApplicationArguments), \
      bRunInShell and " (in child process)" or "",
      a0sExpectedBugIdAndLocations and " => ".join(a0sExpectedBugIdAndLocations) or "no bugs"
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
  def fCdbStdInInputCallback(oBugId, sbInput):
    sInput = fsCP437FromBytesString(sbInput);
    if mGlobals.bShowCdbIO: oConsole.fOutput("stdin<%s" % sInput);
    asLog.append("stdin<%s" % sInput);
  def fCdbStdOutOutputCallback(oBugId, sbOutput):
    sOutput = fsCP437FromBytesString(sbOutput);
    if mGlobals.bShowCdbIO: oConsole.fOutput("stdout>%s" % sOutput);
    asLog.append("stdout>%s" % sOutput);
  def fCdbStdErrOutputCallback(oBugId, sbOutput):
    sOutput = fsCP437FromBytesString(sbOutput);
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
      oConsole.fOutput(WARN, "\u2554\u2550\u2550[ ", WARN_INFO, "License warning", WARN, " ]", sPadding = "\u2550");
      for sLicenseWarning in asLicenseWarnings:
        oConsole.fOutput(WARN, "\u2551 ", WARN_INFO, sLicenseWarning);
      oConsole.fOutput(WARN, "\u255A", sPadding = "\u2550");
      mGlobals.bLicenseWarningsShown = True;
  def fLicenseErrorsCallback(oBugId, asLicenseErrors):
    oConsole.fOutput(ERROR, "\u2554\u2550\u2550[ ", ERROR_INFO, "License warning", ERROR, " ]", sPadding = "\u2550");
    for sLicenseError in asLicenseErrors:
      oConsole.fOutput(ERROR, "\u2551 ", ERROR_INFO, sLicenseError);
    oConsole.fOutput(ERROR, "\u255A", sPadding = "\u2550");
    os._exit(1);
  
  def fInternalExceptionCallback(oBugId, oThread, oException, oTraceBack):
    if not mGlobals.bShowCdbIO: 
      for sLine in asLog:
        oConsole.fOutput(sLine);
    oBugId.fStop();
    if m0DebugOutput:
      m0DebugOutput.fTerminateWithException(oException, guExitCodeInternalError, bShowStacksForAllThread = True);
    raise oException;
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
    if a0sExpectedBugIdAndLocations:
      for sExpectedBugIdAndLocation in a0sExpectedBugIdAndLocations:
        oConsole.fOutput("  => %s" % sExpectedBugIdAndLocation);
    oConsole.fOutput("-" * 80);
  bBugIdStarted = False;
  bBugIdStopped = False;
  try:
    oBugId = cBugId(
      sCdbISA = sISA, # Debug with a cdb.exe for an ISA that matches the target process.
      s0ApplicationBinaryPath = sApplicationBinaryPath,
      asApplicationArguments = asApplicationArguments,
      azsSymbolServerURLs = ["http://msdl.microsoft.com/download/symbols"], # Will be ignore if symbols are disabled.
      bGenerateReportHTML = mGlobals.bGenerateReportHTML,
      u0TotalMaxMemoryUse = mGlobals.uTotalMaxMemoryUse,
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
        s0ExpectedBugIdAndLocation = a0sExpectedBugIdAndLocations[uCounter] if uCounter < len(a0sExpectedBugIdAndLocations) else None;
        o0BugReport = aoBugReports[uCounter] if uCounter < len(aoBugReports) else None;
        if not s0ExpectedBugIdAndLocation and not o0BugReport:
          break;
        uCounter += 1;
        s0DetectedBugIdAndLocation = (
          "%s @ %s" % (o0BugReport.sId, o0BugReport.s0BugLocation or "(unknown)") if o0BugReport is not None else
          None
        );
        oConsole.fOutput("  Bug #%d %s:" % (
          uCounter,
          (
            "is as expected" if s0DetectedBugIdAndLocation == s0ExpectedBugIdAndLocation else
            "was not detected" if s0DetectedBugIdAndLocation is None else
            "was not expected" if s0ExpectedBugIdAndLocation is None else
            "has an unexpected bug id/location"
          ),
        ));
        if s0ExpectedBugIdAndLocation:
          oConsole.fOutput("  Expected: %s" % (repr(s0ExpectedBugIdAndLocation)));
        else:
          oConsole.fOutput("  Expected: no bug.");
        if o0BugReport:
          oConsole.fOutput("  Detected: %ss" % repr(s0DetectedBugIdAndLocation));
          oConsole.fOutput("            (Description: %s)" % repr(o0BugReport.s0BugDescription));
        else:
          oConsole.fOutput("  Detected: no bug.");
    if sExpectedFailedToDebugApplicationErrorMessage:
      pass;
    elif a0sExpectedBugIdAndLocations is None:
      uCounter = 0;
      oConsole.fOutput("* Test results for: %s" % sTestDescription);
      for oBugReport in aoBugReports:
        uCounter += 1;
        sBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.s0BugLocation or "(unknown)");
        oConsole.fOutput("  Test bug #%d: %s." % (uCounter, repr(sBugIdAndLocation)));
        if oBugReport.o0Stack:
          fOutputStack(oBugReport.o0Stack);
    else:
      if len(aoBugReports) != len(a0sExpectedBugIdAndLocations):
        if not mGlobals.bShowCdbIO: 
          for sLine in asLog:
            oConsole.fOutput(sLine);
        oConsole.fOutput(ERROR, "- Failed test: %s" % sTestDescription);
        oConsole.fOutput(ERROR, "  Test reported %d instead of %d bugs in the application." % (len(aoBugReports), len(a0sExpectedBugIdAndLocations)));
        fDumpExpectedAndReported();
        raise AssertionError("Test reported different number of bugs than was expected");
      else:
        uCounter = 0;
        for uCounter in range(len(a0sExpectedBugIdAndLocations)):
          sExpectedBugIdAndLocation = a0sExpectedBugIdAndLocations[uCounter];
          rExpectedBugIdAndLocation = re.compile("^(%s)$" % sExpectedBugIdAndLocation.replace("<binary>", re.escape(sTestBinaryName)));
          oBugReport = aoBugReports[uCounter];
          s0DetectedBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.s0BugLocation or "(unknown)");
          if not rExpectedBugIdAndLocation.match(s0DetectedBugIdAndLocation):
            if not mGlobals.bShowCdbIO: 
              for sLine in asLog:
                oConsole.fOutput(ERROR, sLine);
            oConsole.fOutput(ERROR, "- Failed test: %s" % sTestDescription);
            oConsole.fOutput(ERROR, "  Test bug #%d does not match %s." % (uCounter, repr(sExpectedBugIdAndLocation)));
            fDumpExpectedAndReported()
            if oBugReport.o0Stack:
              fOutputStack(oBugReport.o0Stack);
            raise AssertionError("Test reported unexpected Bug Id and/or Location.");
    if mGlobals.bSaveReportHTML:
      for oBugReport in aoBugReports:
        # We'd like a report file name base on the BugId, but the later may contain characters that are not valid in a file name
        sDesiredReportFileName = "%s %s @ %s.html" % (sISA, oBugReport.sId, oBugReport.s0BugLocation or "(unknown)");
        # Thus, we need to translate these characters to create a valid filename that looks very similar to the BugId
        sValidReportFileName = cFileSystemItem.fsGetValidName(sDesiredReportFileName, bUseUnicodeHomographs = False);
        sReportsFilePath = os.path.join(mGlobals.sReportsFolderPath, sValidReportFileName);
        oReportFile = cFileSystemItem(sReportsFilePath);
        sbReportHTML = bytes(oBugReport.sReportHTML, "utf-8");
        if oReportFile.fbIsFile(bParseZipFiles = True):
          oReportFile.fbWrite(sbReportHTML, bKeepOpen = False, bParseZipFiles = True, bThrowErrors = True);
        else:
          oReportFile.fbCreateAsFile(sbReportHTML, bCreateParents = True, bParseZipFiles = True, bKeepOpen = False, bThrowErrors = True);
        oConsole.fOutput("  Wrote report: %s" % sReportsFilePath);
  except Exception as oException:
    if bBugIdStarted and not bBugIdStopped:
      oBugId.fTerminate();
    oConsole.fOutput(ERROR, "- Failed test: %s" % sTestDescription);
    oConsole.fOutput(ERROR, "  Exception:   %s" % repr(oException));
    raise;
  finally:
    if mGlobals.bDebugStartFinish:
      oConsole.fOutput("* Finished %s" % sTestDescription);
    elif a0sExpectedBugIdAndLocations is not None:
      oConsole.fOutput("+ %s" % sTestDescription);
