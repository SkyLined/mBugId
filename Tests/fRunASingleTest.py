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
INFO = 0x0F0F;
STATUS = 0x0F0B;
OK = 0x0F0A;
ERROR = 0x0F0C;
WARN = 0x0F06;
WARN_INFO = 0x0F0E;
ERROR_INFO = 0x0F0F;

mGlobals.bLicenseWarningsShown = False;

def fOutputStack(oStack):
  oConsole.fOutput(INFO, "  Stack:");
  for oStackFrame in oStack.aoFrames:
    oConsole.fOutput(
      NORMAL, "  \u2022 ",
      NORMAL if oStackFrame.bHidden else INFO, fsCP437FromBytesString(oStackFrame.sb0UniqueAddress or b"---"),
      NORMAL, " (cdb:", NORMAL if oStackFrame.sb0UniqueAddress else INFO, fsCP437FromBytesString(oStackFrame.sbCdbSymbolOrAddress), NORMAL, ")",
      [" => ", oStackFrame.s0IsHiddenBecause] if oStackFrame.s0IsHiddenBecause else [], 
    );

guExitCodeInternalError = 1; # Use standard value;
def fRunASingleTest(
  sISA,
  asApplicationArguments,
  a0sExpectedBugIdAndLocations,
  s0ExpectedFailedToDebugApplicationErrorMessage = None,
  bRunInShell = False,
  s0ApplicationBinaryPath = None,
  bASan = False,
  uMaximumNumberOfBugs = 2,
  bExcessiveCPUUsageChecks = False,
  bEnableVerboseOutput = False,
):
  assert s0ApplicationBinaryPath is None or not bASan, \
      "Setting bASan when supplying an application binary path makes no sense";
  sApplicationBinaryPath = (
    s0ApplicationBinaryPath if s0ApplicationBinaryPath is not None else 
    mGlobals.dsASanTestsBinaries_by_sISA[sISA] if bASan else
    mGlobals.dsTestsBinaries_by_sISA[sISA]
  );
  if s0ExpectedFailedToDebugApplicationErrorMessage:
    axTestDescription = [
      INFO, sISA,
      NORMAL, " Run ",
      INFO, " ".join([sApplicationBinaryPath] + asApplicationArguments),
      NORMAL, " => ",
      INFO, repr(s0ExpectedFailedToDebugApplicationErrorMessage),
    ];
  else:
    axTestDescription = [
      INFO, sISA,
      NORMAL, " ",
      [
        INFO, "ASan",
        NORMAL, " ",
      ] if bASan else [],
      INFO, " ".join(asApplicationArguments),
      [
        NORMAL, " (in ",
        INFO, "child",
        NORMAL, " process)"
      ] if bRunInShell else [],
      [
        [
          NORMAL, " => ",
          INFO, sExpectedBugIdAndLocation,
        ] for sExpectedBugIdAndLocation in a0sExpectedBugIdAndLocations
      ] if a0sExpectedBugIdAndLocations else [
        NORMAL, " => ",
        INFO, "no bugs",
      ],
    ];
  
  sTestBinaryName = os.path.basename(sApplicationBinaryPath).lower();
  
  if bRunInShell:
    asApplicationArguments = ["/C", sApplicationBinaryPath] + asApplicationArguments; 
    sApplicationBinaryPath = mGlobals.dsComSpec_by_sISA[sISA];
  
  oConsole.fSetTitle(axTestDescription);
  if mGlobals.bDebugStartFinish:
    oConsole.fOutput(
      STATUS, "→",
      NORMAL, " Started ",
      axTestDescription,
      NORMAL, ".",
    );
  
  asLog = [];
  def fDumpLog():
    oConsole.fOutput("\u2554\u2550\u2550[ CDB LOG ", sPadding = "\u2550");
    for sLine in asLog:
      oConsole.fOutput("\u2551 ", sLine);
    oConsole.fOutput("\u255A", sPadding = "\u2550");
  def fCdbStdInInputCallback(oBugId, sbInput):
    sInput = fsCP437FromBytesString(sbInput);
    if mGlobals.bShowCdbIO or bEnableVerboseOutput: oConsole.fOutput("  stdin<%s" % sInput);
    asLog.append("stdin<%s" % sInput);
  def fCdbStdOutOutputCallback(oBugId, sbOutput):
    sOutput = fsCP437FromBytesString(sbOutput);
    if mGlobals.bShowCdbIO or bEnableVerboseOutput: oConsole.fOutput("  stdout>%s" % sOutput);
    asLog.append("stdout>%s" % sOutput);
  def fCdbStdErrOutputCallback(oBugId, sbOutput):
    sOutput = fsCP437FromBytesString(sbOutput);
    if mGlobals.bShowCdbIO or bEnableVerboseOutput: oConsole.fOutput("  stderr>%s" % sOutput);
    asLog.append("stderr>%s" % sOutput);
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
      if mGlobals.bShowApplicationIO or bEnableVerboseOutput: oConsole.fOutput(sLogLine);
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
    if mGlobals.bShowApplicationIO or bEnableVerboseOutput: oConsole.fOutput(sLogLine);
    asLog.append(sLogLine);
  def fApplicationStdOutOutputCallback(oBugId, oConsoleProcess, bIsMainProcess, sOutput):
    # This is always a main process
    sLogLine = "%s process 0x%X (%s): stdout> %s" % (
      bIsMainProcess and "Main" or "Sub",
      oConsoleProcess.uId,
      oConsoleProcess.sCommandLine,
      sOutput
    )
    if mGlobals.bShowApplicationIO or bEnableVerboseOutput: oConsole.fOutput(sLogLine);
    asLog.append(sLogLine);
  def fApplicationSuspendedCallback(oBugId, sReason):
    asLog.append("Application suspended (%s)" % sReason);
  def fApplicationResumedCallback(oBugId):
    asLog.append("Application resumed");
  def fApplicationRunningCallback(oBugId):
    asLog.append("Application running");
  def fFailedToDebugApplicationCallback(oBugId, sErrorMessage):
    if s0ExpectedFailedToDebugApplicationErrorMessage == sErrorMessage:
      return;
    if not mGlobals.bShowCdbIO: 
      fDumpLog();
    oConsole.fOutput(
      ERROR, "×",
      NORMAL, " Failed test: ",
      axTestDescription,
      NORMAL, ":",
    );
    oConsole.fOutput(
      "  BugId failed to debug the application.",
    );
    if s0ExpectedFailedToDebugApplicationErrorMessage:
      oConsole.fOutput(
        "  Expected error: ",
        INFO, repr(s0ExpectedFailedToDebugApplicationErrorMessage),
        NORMAL, ".",
      );
      oConsole.fOutput(
        "  Actual error:    ",
        INFO, repr(sErrorMessage),
        NORMAL, ".",
      );
    else:
      oConsole.fOutput(
        "  Error: ",
        INFO, repr(sErrorMessage),
        NORMAL, ".",
      );
    oBugId.fStop();
    raise AssertionError(sErrorMessage);
  def fFailedToApplyMemoryLimitsCallback(oBugId, oProcess):
    if not mGlobals.bShowCdbIO: 
      fDumpLog();
    oConsole.fOutput(
      ERROR, "×",
      NORMAL, " Failed to apply memory limits to process ",
      INFO, "0x%X" % oProcess.uId,
      NORMAL, " (",
      INFO, oProcess.sCommandLine,
      NORMAL, ") for test: ",
      axTestDescription,
      NORMAL, ".",
    );
    oBugId.fStop();
    raise AssertionError("Failed to apply memory limits to process");
  def fFinishedCallback(oBugId):
    if mGlobals.bShowCdbIO: oConsole.fOutput("  Finished");
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
      fDumpLog();
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
    if mGlobals.bShowCdbIO or bEnableVerboseOutput: oConsole.fOutput(sLogLine);
    asLog.append(sLogLine);
  
  aoBugReports = [];
  def fBugReportCallback(oBugId, oBugReport):
    if bEnableVerboseOutput: oConsole.fOutput("Bug reported: %s" % oBugReport);
    aoBugReports.append(oBugReport);
  def fBugCannotBeIgnoreCallback(oBugId, sMessage):
    if bEnableVerboseOutput: oConsole.fOutput("Bug cannot be ignored: %s" % sMessage);
  
  if mGlobals.bShowCdbIO:
    oConsole.fOutput();
    oConsole.fOutput(
      INFO, "=" * 80,
    );
    oConsole.fOutput(
      INFO, sApplicationBinaryPath, " ".join(asApplicationArguments),
    );
    if a0sExpectedBugIdAndLocations:
      for sExpectedBugIdAndLocation in a0sExpectedBugIdAndLocations:
        oConsole.fOutput(
          "  => ",
          INFO, sExpectedBugIdAndLocation,
        );
    oConsole.fOutput(
      INFO, "-" * 80,
    );
  bBugIdStarted = False;
  bBugIdStopped = False;
  try:
    oBugId = cBugId(
      sCdbISA = sISA, # Debug with a cdb.exe for an ISA that matches the target process.
      s0ApplicationBinaryPath = sApplicationBinaryPath,
      asApplicationArguments = asApplicationArguments,
      bDoNotLoadSymbols = mGlobals.bDoNotLoadSymbols,
      azsSymbolServerURLs = ["http://msdl.microsoft.com/download/symbols"], # Will be ignore if symbols are disabled.
      bGenerateReportHTML = mGlobals.bGenerateReportHTML,
      u0TotalMaxMemoryUse = mGlobals.uTotalMaxMemoryUse,
      u0MaximumNumberOfBugs = uMaximumNumberOfBugs,
    );
    oBugId.fAddCallback("Application resumed", fApplicationResumedCallback);
    oBugId.fAddCallback("Application running", fApplicationRunningCallback);
    oBugId.fAddCallback("Application debug output", fApplicationDebugOutputCallback);
    oBugId.fAddCallback("Application stderr output", fApplicationStdErrOutputCallback);
    oBugId.fAddCallback("Application stdout output", fApplicationStdOutOutputCallback);
    oBugId.fAddCallback("Application suspended", fApplicationSuspendedCallback);
    oBugId.fAddCallback("Bug report", fBugReportCallback);
    oBugId.fAddCallback("Bug cannot be ignored", fBugCannotBeIgnoreCallback);
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
    if mGlobals.bShowCdbIO: oConsole.fOutput(
      "= Finished ".ljust(80, "="),
    );
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
        oConsole.fOutput(
          "  Expected: ",
          INFO, repr(s0ExpectedBugIdAndLocation) if s0ExpectedBugIdAndLocation else "no bug",
          NORMAL, ".",
        );
        oConsole.fOutput(
          "  Detected: ",
          INFO, repr(s0DetectedBugIdAndLocation) if o0BugReport else "no bug",
          NORMAL, ".",
        );
        if o0BugReport:
          oConsole.fOutput(
            "            (Description: ",
            INFO, repr(o0BugReport.s0BugDescription),
            NORMAL, ")",
          );
    if s0ExpectedFailedToDebugApplicationErrorMessage:
      pass;
    elif a0sExpectedBugIdAndLocations is None:
      uCounter = 0;
      oConsole.fOutput(
        "→ Test results for ",
        axTestDescription,
        NORMAL, ".",
      );
      for oBugReport in aoBugReports:
        uCounter += 1;
        sBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.s0BugLocation or "(unknown)");
        oConsole.fOutput(
          "  Test bug #",
          INFO, str(uCounter),
          NORMAL, ": ",
          INFO, repr(sBugIdAndLocation),
          NORMAL, ".",
        );
        if oBugReport.o0Stack:
          fOutputStack(oBugReport.o0Stack);
    else:
      if len(aoBugReports) != len(a0sExpectedBugIdAndLocations):
        if not mGlobals.bShowCdbIO: 
          fDumpLog();
        oConsole.fOutput(
          ERROR, "×",
          NORMAL, " Failed test ",
          axTestDescription,
          NORMAL, ":",
        );
        oConsole.fOutput(
          "  Test reported ",
          INFO, str(len(aoBugReports)),
          NORMAL, " instead of ",
          INFO, str(len(a0sExpectedBugIdAndLocations)),
          NORMAL, " bugs in the application."
        );
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
              fDumpLog();
            oConsole.fOutput(
              ERROR, "×",
              NORMAL, " Failed test ",
              axTestDescription,
              NORMAL, ":",
            );
            oConsole.fOutput(
              "  Test bug #",
              INFO, str(uCounter),
              NORMAL, " does not match ",
              INFO, repr(sExpectedBugIdAndLocation),
              NORMAL, ".",
            );
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
        if oReportFile.fbIsFile():
          oReportFile.fWrite(sbReportHTML);
        else:
          oReportFile.fCreateAsFile(sbReportHTML, bCreateParents = True);
        oConsole.fOutput("→ Wrote report: %s" % sReportsFilePath);
  except Exception as oException:
    if bBugIdStarted and not bBugIdStopped:
      oBugId.fTerminate();
    oConsole.fOutput(
      ERROR, "×",
      NORMAL, " Failed test: ",
      axTestDescription,
      NORMAL, ".",
    );
    oConsole.fOutput(
      "  Exception:   ",
      INFO, repr(oException),
    );
    raise;
  finally:
    if mGlobals.bDebugStartFinish:
      oConsole.fOutput(
        NORMAL, "  ",
        OK, "√",
        NORMAL, " Finished, ",
        axTestDescription,
        NORMAL, ".",
      );
    elif a0sExpectedBugIdAndLocations is not None:
      oConsole.fOutput(
        OK, "√",
        NORMAL, " ",
        axTestDescription,
        NORMAL, ".",
      );
