import os, re, time;
from mBugId import cBugId;
from mConsole import oConsole;
from mFileSystemItem import cFileSystemItem;
from mBugId.mCP437 import fsCP437FromBytesString;

import mGlobals;

try: # mDebugOutput use is Optional
  import mDebugOutput as m0DebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  m0DebugOutput = None;

COLOR_NORMAL = 0x0F07;
COLOR_INFO = 0x0F0F;
COLOR_DIM = 0x0F08;
COLOR_STATUS = 0x0F0B;
COLOR_OK = 0x0F0A;
COLOR_ERROR = 0x0F0C;
COLOR_WARN = 0x0F06;
COLOR_WARN_INFO = 0x0F0E;
COLOR_ERROR_INFO = 0x0F0F;

mGlobals.bLicenseWarningsShown = False;

asActivityCharacters = ["⢎⠁", "⠎⠑", "⠊⠱", "⠈⡱", "⢀⡱", "⢄⡰", "⢆⡠", "⢎⡀"];

def fOutputStack(oStack):
  oConsole.fOutput(COLOR_INFO, "  Stack:");
  for oStackFrame in oStack.aoFrames:
    oConsole.fOutput(
      COLOR_NORMAL, "  • ",
      COLOR_NORMAL if oStackFrame.bHidden else COLOR_INFO, fsCP437FromBytesString(oStackFrame.sb0UniqueAddress or b"---"),
      COLOR_NORMAL, " (cdb:", COLOR_NORMAL if oStackFrame.sb0UniqueAddress else COLOR_INFO, fsCP437FromBytesString(oStackFrame.sbCdbSymbolOrAddress), COLOR_NORMAL, ")",
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
  n0ExpectedMaximumTestTime = None,
  bExcessiveCPUUsageChecks = False,
  bEnableVerboseOutput = False,
  bShowActivity = False,
):
  nStartTimeInSeconds = time.time();
  assert s0ApplicationBinaryPath is None or not bASan, \
      "Setting bASan when supplying an application binary path makes no sense";
  sApplicationBinaryPath = (
    s0ApplicationBinaryPath if s0ApplicationBinaryPath is not None else 
    mGlobals.dsASanTestsBinaries_by_sISA[sISA] if bASan else
    mGlobals.dsTestsBinaries_by_sISA[sISA]
  );
  if s0ExpectedFailedToDebugApplicationErrorMessage:
    axTestDescription = [
      COLOR_INFO, sISA,
      COLOR_NORMAL, " Run ",
      COLOR_INFO, " ".join([sApplicationBinaryPath] + asApplicationArguments),
      COLOR_NORMAL, " => ",
      COLOR_INFO, repr(s0ExpectedFailedToDebugApplicationErrorMessage),
    ];
  else:
    axTestDescription = [
      COLOR_INFO, sISA,
      COLOR_NORMAL, " ",
      [
        COLOR_INFO, "ASan",
        COLOR_NORMAL, " ",
      ] if bASan else [],
      COLOR_INFO, " ".join(asApplicationArguments),
      [
        COLOR_NORMAL, " (in ",
        COLOR_INFO, "child",
        COLOR_NORMAL, " process)"
      ] if bRunInShell else [],
      [
        [
          COLOR_NORMAL, " => ",
          COLOR_INFO, sExpectedBugIdAndLocation,
        ] for sExpectedBugIdAndLocation in a0sExpectedBugIdAndLocations
      ] if a0sExpectedBugIdAndLocations else [
        COLOR_NORMAL, " => ",
        COLOR_INFO, "no bugs",
      ],
    ];
  
  sTestBinaryName = os.path.basename(sApplicationBinaryPath).lower();
  
  if bRunInShell:
    asApplicationArguments = ["/C", sApplicationBinaryPath] + asApplicationArguments; 
    sApplicationBinaryPath = mGlobals.dsComSpec_by_sISA[sISA];
  
  oConsole.fSetTitle(axTestDescription);
  if mGlobals.bDebugStartFinish:
    oConsole.fOutput(
      COLOR_STATUS, "→",
      COLOR_NORMAL, " Started ",
      axTestDescription,
      COLOR_NORMAL, ".",
    );
  
  asLog = [];
  def fDumpLog():
    oConsole.fOutput("┌──[ CDB LOG ]", sPadding = "─");
    for sLine in asLog:
      oConsole.fOutput("│ ", sLine);
    oConsole.fOutput("└", sPadding = "─");
  def fCdbActivityCallback(oBugId, nTimeSinceStartOfCdbActivityInSeconds):
    uActivityIndex = int(time.time() * 10);
    oConsole.fStatus(
      COLOR_STATUS, asActivityCharacters[uActivityIndex % len(asActivityCharacters)],
      axTestDescription,
      COLOR_NORMAL, ": Process time: ",
      COLOR_INFO, "%.2fs" % oBugId.fnApplicationRunTimeInSeconds(),
      COLOR_NORMAL, ", current cdb command time: ",
      COLOR_INFO, "%.2fs" % nTimeSinceStartOfCdbActivityInSeconds,
      COLOR_NORMAL, ".",
    );
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
  def fApplicationDebugOutputCallback(oBugId, oProcess, bIsMainProcess, asbOutput):
    bFirstLine = True;
    for sbOutput in asbOutput:
      sOutput = fsCP437FromBytesString(sbOutput);
      oConsole.fOutput(COLOR_DIM, f"debug> {sOutput}");
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
    oConsole.fOutput(COLOR_ERROR, f"stderr> {sOutput}");
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
    oConsole.fOutput(COLOR_INFO, f"stdout> {sOutput}");
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
    oConsole.fOutput(
      COLOR_ERROR, "✘",
      COLOR_NORMAL, " Failed to debug application in test: ",
      axTestDescription,
      COLOR_NORMAL, "!",
    );
    if not mGlobals.bShowCdbIO: 
      fDumpLog();
    oConsole.fOutput(
      "  BugId failed to debug the application.",
    );
    if s0ExpectedFailedToDebugApplicationErrorMessage:
      oConsole.fOutput(
        "  Expected error: ",
        COLOR_INFO, repr(s0ExpectedFailedToDebugApplicationErrorMessage),
        COLOR_NORMAL, ".",
      );
      oConsole.fOutput(
        "  Actual error:    ",
        COLOR_INFO, repr(sErrorMessage),
        COLOR_NORMAL, ".",
      );
    else:
      oConsole.fOutput(
        "  Error: ",
        COLOR_INFO, repr(sErrorMessage),
        COLOR_NORMAL, ".",
      );
    oBugId.fStop();
    raise AssertionError(sErrorMessage);
  def fFailedToApplyMemoryLimitsCallback(oBugId, oProcess):
    oConsole.fOutput(
      COLOR_ERROR, "✘",
      COLOR_NORMAL, " Failed to apply memory limits for test: ",
      axTestDescription,
      COLOR_NORMAL, "!",
    );
    if not mGlobals.bShowCdbIO: 
      fDumpLog();
    oConsole.fOutput(
      COLOR_ERROR, "  ✘",
      COLOR_NORMAL, " Failed to apply memory limits to process ",
      COLOR_INFO, "0x%X" % oProcess.uId,
      COLOR_NORMAL, " (",
      COLOR_INFO, oProcess.sCommandLine,
      COLOR_NORMAL, ") for test: ",
      axTestDescription,
      COLOR_NORMAL, ".",
    );
    oBugId.fStop();
    raise AssertionError("Failed to apply memory limits to process");
  def fFinishedCallback(oBugId):
    if mGlobals.bShowCdbIO: oConsole.fOutput("  Finished");
    asLog.append("Finished");
  def fLicenseWarningsCallback(oBugId, asLicenseWarnings):
    if not mGlobals.bLicenseWarningsShown:
      oConsole.fOutput(COLOR_WARN, "┌──[ ", COLOR_WARN_INFO, "License warning", COLOR_WARN, " ]", sPadding = "─");
      for sLicenseWarning in asLicenseWarnings:
        oConsole.fOutput(COLOR_WARN, "│ ", COLOR_WARN_INFO, sLicenseWarning);
      oConsole.fOutput(COLOR_WARN, "└", sPadding = "─");
      mGlobals.bLicenseWarningsShown = True;
  def fLicenseErrorsCallback(oBugId, asLicenseErrors):
    oConsole.fOutput(COLOR_ERROR, "┌──[ ", COLOR_ERROR_INFO, "License warning", COLOR_ERROR, " ]", sPadding = "─");
    for sLicenseError in asLicenseErrors:
      oConsole.fOutput(COLOR_ERROR, "│ ", COLOR_ERROR_INFO, sLicenseError);
    oConsole.fOutput(COLOR_ERROR, "└", sPadding = "─");
    os._exit(1);
  
  def fInternalExceptionCallback(oBugId, oThread, oException, oTraceBack):
    oConsole.fOutput(
      COLOR_ERROR, "✘",
      COLOR_NORMAL, " Internal exception while running test: ",
      axTestDescription,
      COLOR_NORMAL, "!",
    );
    if not mGlobals.bShowCdbIO: 
      fDumpLog();
    oConsole.fOutput(
      "  Internal exception:   ",
      COLOR_INFO, repr(oException),
    );
    oBugId.fStop();
    if m0DebugOutput:
      m0DebugOutput.fTerminateWithException(oException, guExitCodeInternalError, bShowStacksForAllThread = True);
    raise oException;
  def fPageHeapNotEnabledCallback(oBugId, oProcess, bIsMainProcess, bPreventable):
    oConsole.fOutput(
      COLOR_ERROR,  "✘",
      COLOR_NORMAL, " It appears you have not enabled page heap for ",
      COLOR_INFO,   oProcess.sBinaryName,
      COLOR_NORMAL, " which is required to run tests.",
    );
    oBugId.fStop();
    os._exit(1);
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
      COLOR_INFO, "═" * 80,
    );
    oConsole.fOutput(
      COLOR_INFO, sApplicationBinaryPath, " ", " ".join(asApplicationArguments),
    );
    if a0sExpectedBugIdAndLocations:
      for sExpectedBugIdAndLocation in a0sExpectedBugIdAndLocations:
        oConsole.fOutput(
          "  => ",
          COLOR_INFO, sExpectedBugIdAndLocation,
        );
    oConsole.fOutput(
      COLOR_INFO, "═" * 80,
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
    if bShowActivity:
      oBugId.fAddCallback("Cdb activity", fCdbActivityCallback);
      oBugId.fSetActivityReportInterval(0.1);
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
      "═══[ Finished ]".ljust(80, "═"),
    );
    def fDumpExpectedAndReported(sTestBinaryName):
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
          COLOR_INFO, repr(s0ExpectedBugIdAndLocation.replace("<binary>", sTestBinaryName)) if s0ExpectedBugIdAndLocation else "no bug",
          COLOR_NORMAL, ".",
        );
        oConsole.fOutput(
          "  Detected: ",
          COLOR_INFO, repr(s0DetectedBugIdAndLocation) if o0BugReport else "no bug",
          COLOR_NORMAL, ".",
        );
        if o0BugReport:
          oConsole.fOutput(
            "            (Description: ",
            COLOR_INFO, repr(o0BugReport.s0BugDescription),
            COLOR_NORMAL, ")",
          );
    if s0ExpectedFailedToDebugApplicationErrorMessage:
      pass;
    elif a0sExpectedBugIdAndLocations is None:
      uCounter = 0;
      oConsole.fOutput(
        "→ Test results for ",
        axTestDescription,
        COLOR_NORMAL, ".",
      );
      for oBugReport in aoBugReports:
        uCounter += 1;
        sBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.s0BugLocation or "(unknown)");
        oConsole.fOutput(
          "  Test bug #",
          COLOR_INFO, str(uCounter),
          COLOR_NORMAL, ": ",
          COLOR_INFO, repr(sBugIdAndLocation),
          COLOR_NORMAL, ".",
        );
        if oBugReport.o0Stack:
          fOutputStack(oBugReport.o0Stack);
    else:
      if len(aoBugReports) != len(a0sExpectedBugIdAndLocations):
        oConsole.fOutput(
          COLOR_ERROR, "✘",
          COLOR_NORMAL, " Unexpected number of bugs reported in test ",
          axTestDescription,
          COLOR_NORMAL, "!",
        );
        if not mGlobals.bShowCdbIO: 
          fDumpLog();
        oConsole.fOutput(
          "  Test reported ",
          COLOR_INFO, str(len(aoBugReports)),
          COLOR_NORMAL, " instead of ",
          COLOR_INFO, str(len(a0sExpectedBugIdAndLocations)),
          COLOR_NORMAL, " bugs in the application."
        );
        fDumpExpectedAndReported(sTestBinaryName);
        raise AssertionError("Test reported different number of bugs than was expected");
      else:
        uCounter = 0;
        for uCounter in range(len(a0sExpectedBugIdAndLocations)):
          sExpectedBugIdAndLocation = a0sExpectedBugIdAndLocations[uCounter];
          rExpectedBugIdAndLocation = re.compile("^(%s)$" % sExpectedBugIdAndLocation.replace("<binary>", re.escape(sTestBinaryName)));
          oBugReport = aoBugReports[uCounter];
          s0DetectedBugIdAndLocation = "%s @ %s" % (oBugReport.sId, oBugReport.s0BugLocation or "(unknown)");
          if not rExpectedBugIdAndLocation.match(s0DetectedBugIdAndLocation):
            oConsole.fOutput(
              COLOR_ERROR, "✘",
              COLOR_NORMAL, " Unexpected BugId in test ",
              axTestDescription,
              COLOR_NORMAL, "!",
            );
            if not mGlobals.bShowCdbIO:
              fDumpLog();
            oConsole.fOutput(
              "  Test bug #",
              COLOR_INFO, str(uCounter),
              COLOR_NORMAL, " does not match ",
              COLOR_INFO, repr(sExpectedBugIdAndLocation),
              COLOR_NORMAL, ".",
            );
            fDumpExpectedAndReported(sTestBinaryName)
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
      COLOR_ERROR, "✘",
      COLOR_NORMAL, " Internal error in test: ",
      axTestDescription,
      COLOR_NORMAL, ".",
    );
    oConsole.fOutput(
      "  Exception:   ",
      COLOR_INFO, repr(oException),
    );
    raise;
  finally:
    nTestTimeInSeconds = time.time() - nStartTimeInSeconds;
    if mGlobals.bDebugStartFinish:
      oConsole.fOutput(
        COLOR_NORMAL, "  ",
        COLOR_OK, "✓",
        COLOR_NORMAL, " Finished, ",
        axTestDescription,
        COLOR_NORMAL, " in ",
        (
          COLOR_ERROR if n0ExpectedMaximumTestTime is not None and nTestTimeInSeconds > n0ExpectedMaximumTestTime else
          COLOR_NORMAL
        ),
        "%f" % nTestTimeInSeconds,
        COLOR_NORMAL, " seconds.",
      );
    elif a0sExpectedBugIdAndLocations is not None:
      oConsole.fOutput(
        COLOR_OK, "✓",
        COLOR_NORMAL, " ",
        axTestDescription,
        COLOR_NORMAL, " in ",
        (
          COLOR_ERROR if n0ExpectedMaximumTestTime is not None and nTestTimeInSeconds > n0ExpectedMaximumTestTime else
          COLOR_NORMAL
        ),
        "%f" % nTestTimeInSeconds,
        COLOR_NORMAL, " seconds.",
      );
    uCounter = 0;
    for oBugReport in aoBugReports:
      
      oConsole.fOutput(
        "  %s─%s @ %s" % (
          "└" if oBugReport == aoBugReports[-1] else "├",
          oBugReport.sId,
          oBugReport.s0BugLocation or "(unknown)"
        )
      );