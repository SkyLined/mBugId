import os, sys;
sModulePath = os.path.dirname(__file__);
sys.path = [sModulePath] + [sPath for sPath in sys.path if sPath.lower() != sModulePath.lower()];

from fTestDependencies import fTestDependencies;
fTestDependencies("--automatically-fix-dependencies" in sys.argv);
sys.argv = [s for s in sys.argv if s != "--automatically-fix-dependencies"];

try: # mDebugOutput use is Optional
  import mDebugOutput as m0DebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  m0DebugOutput = None;

COLOR_NORMAL = 0x0F07;
COLOR_INFO = 0x0F0F;
COLOR_STATUS = 0x0F0B;
COLOR_OK = 0x0F0A;
COLOR_ERROR = 0x0F0C;
COLOR_WARN = 0x0F06;
COLOR_WARN_INFO = 0x0F0E;
COLOR_ERROR_INFO = 0x0F0F;

guExitCodeInternalError = 1; # Use standard value;
gnMaxCPUUsageTestTimeInSeconds = 20; # This will take a bit of time to analyze.
try:
  try:
    from mConsole import oConsole;
  except:
    import sys, threading;
    oConsoleLock = threading.Lock();
    class oConsole(object):
      @staticmethod
      def fOutput(*txArguments, **dxArguments):
        sOutput = "";
        for x in txArguments:
          if isinstance(x, str):
            sOutput += x;
        sPadding = dxArguments.get("sPadding");
        if sPadding:
          sOutput.ljust(120, sPadding);
        oConsoleLock.acquire();
        print(sOutput);
        sys.stdout.flush();
        oConsoleLock.release();
      @staticmethod
      def fStatus(*txArguments, **dxArguments):
        pass;
  
  import os, platform, sys, time;
  #Import the test subject
  from mBugId import cBugId;
  
  from fShowHelp import fShowHelp;
  from fRunASingleTest import fRunASingleTest;
  import mGlobals;
  
  nStartTimeInSeconds = time.time();
  
  cBugId.dxConfig["bShowAllCdbCommandsInReport"] = True;
  cBugId.dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"] = 0.5; # Excessive CPU usage should be apparent within half a second.
  cBugId.dxConfig["uArchitectureIndependentBugIdBits"] = 32; # Test architecture independent bug ids
  
  from mTestLevels import QUICK, NORMAL, FULL, x86, x64, FULL_x86, FULL_x64;

  sPythonISA = {
    "32bit": "x86",
    "64bit": "x64",
  }[platform.architecture()[0]];
  
  bFailed = False;
  bTestQuick = False;
  bTestFull = False;
  sISA = None;
  bEnableDebugOutput = False;
  bEnableVerboseOutput = False;
  bUseOnlineSymbolPaths = False;
  asApplicationArguments = [];
  for sArgument in sys.argv[1:]:
    if sArgument == "--full": 
      bTestQuick = False;
      bTestFull = True;
      mGlobals.bGenerateReportHTML = True;
    elif sArgument in ["--report", "--reports"]: 
      mGlobals.bGenerateReportHTML = True;
      mGlobals.bSaveReportHTML = True;
    elif sArgument == "--verbose": 
      bEnableVerboseOutput = True;
    elif sArgument == "--quick": 
      bTestQuick = True;
      bTestFull = False;
    elif sArgument == "--no-symbols": 
      mGlobals.bDoNotLoadSymbols = True;
    elif sArgument == "--show-cdb-io": 
      mGlobals.bShowCdbIO = True;
    elif sArgument == "--debug": 
      bEnableDebugOutput = True;
    elif sArgument == "--online": 
      bUseOnlineSymbolPaths = True;
    elif sArgument in ["-?", "/?", "/h", "-h", "--help"]: 
      fShowHelp(oConsole);
      sys.exit(0);
    elif sISA is None:
      sISA = sArgument;
    else:
      asApplicationArguments.append(sArgument);
  
  if sISA is not None:
    oConsole.fOutput("• ISA = %s." % sISA);
  if bTestQuick:
    oConsole.fOutput("• Running quick tests.");
  elif bTestFull:
    oConsole.fOutput("• Running full tests.");
  if mGlobals.bShowCdbIO:
    oConsole.fOutput("• Showing cdb I/O.");
  if bEnableDebugOutput:
    assert m0DebugOutput, \
        "The 'mDebugOutput' moduke is needed to show debug output.";
    m0DebugOutput.fEnableAllDebugOutput();
    oConsole.fOutput("• Showing debug output.");
  if not bUseOnlineSymbolPaths:
    oConsole.fOutput(
      COLOR_WARN,"▲ ",
      COLOR_NORMAL, "NOT using symbol servers or NT_SYMBOL_PATH."
    );
    oConsole.fOutput("  Once symbols have been downloaded, this makes tests execute faster.");
    oConsole.fOutput(
      "  The first time you run these tests, please use ",
      COLOR_INFO, "--online",
      COLOR_NORMAL, " to make sure all relevant symbols are downloaded."
    );
    # disable symbol downloads to speed up testing.
    cBugId.dxConfig["asDefaultSymbolServerURLs"] = [];
    cBugId.dxConfig["bUse_NT_SYMBOL_PATH"] = False;
  if not bTestFull:
    # This speeds up testing a lot.
    cBugId.dxConfig["bCollectInformationAboutPointersInMemoryDumps"] = False;
  else:
    cBugId.dxConfig["bCollectInformationAboutPointersInMemoryDumps"] = True;
  
  # These values are based on previous tests run on my machine and guessing.
  dnTestAdditionalExpectedRunTime_by_sISA = {
    "x64": (
      0
      + (mGlobals.bGenerateReportHTML and 20 or 0) # generating a report takes time
      + (bUseOnlineSymbolPaths and 60 or 0) # I am not sure - this depends on the speed of the internet connection and how many symbols are cached
      + (cBugId.dxConfig["bCollectInformationAboutPointersInMemoryDumps"] and 60 or 0)
    ),
    "x86": (
      1
      + (mGlobals.bGenerateReportHTML and 600 or 0) # generating a report is very slow for unknown reasons
      + (bUseOnlineSymbolPaths and 60 or 0) # I am not sure - this depends on the speed of the internet connection and how many symbols are cached
      + (cBugId.dxConfig["bCollectInformationAboutPointersInMemoryDumps"] and 60 or 0)
    ), # This is a guess
  };

  if len(asApplicationArguments) > 0:
    mGlobals.bShowApplicationIO = True;
    n0ExpectedMaximumTotalTestTimeInSeconds = None;
    fRunASingleTest(
      sISA = sISA,
      asApplicationArguments = asApplicationArguments,
      a0sExpectedBugIdAndLocations = None, # Expect no exceptions.
      s0ExpectedFailedToDebugApplicationErrorMessage = None,
      bRunInShell = False,
      s0ApplicationBinaryPath = None,
      bASan = False,
      n0ExpectedMaximumTestTime = None,
      uMaximumNumberOfBugs = 2,
      bExcessiveCPUUsageChecks = True,
      bEnableVerboseOutput = bEnableVerboseOutput,
    );
    uNumberOfTests = 1;
  else:
    if sISA:
      asTestISAs = [sISA];
    else:
      asTestISAs = {
        "x86": ["x86"],
        "x64": ["x64", "x86"],
      }[sPythonISA];
    # This is used quite often, so we create a variable to store it.
    srMain = r"(540|80a(\.de9)?) @ <binary>!wmain";
    nExpectedNoBinaryTestTimeOnX64 = 0.1; # This should be very quick.
    nExpectedNormalTestTimeOnX64 = 2;
    nExpectedRecursiveTestTimeOnX64 = 3; # More analysis needed, so expected to be slower.
    dxTests = {
      "BinaryIssues": [
        (FULL, [], [], {
          "s0ApplicationBinaryPath": "<invalid>",
          "s0ExpectedFailedToDebugApplicationErrorMessage": \
              "Unable to start a new process for binary path \"<invalid>\": Win32 error 0x7B (ERROR_INVALID_NAME)."
        }, nExpectedNoBinaryTestTimeOnX64),
        (FULL, [], [], {
          "s0ApplicationBinaryPath": "does not exist",
          "s0ExpectedFailedToDebugApplicationErrorMessage": \
              "Unable to start a new process for binary path \"does not exist\": Win32 error 0x2 (ERROR_FILE_NOT_FOUND).",
        }, nExpectedNoBinaryTestTimeOnX64),
      ],
      "Nop": [
        (FULL,   [],      [], nExpectedNormalTestTimeOnX64), # No exceptions, just a clean program exit.
      ],
      "Breakpoint": [
        (QUICK,  [],      [r"Breakpoint " + srMain], {"bRunInShell": bTestFull}, nExpectedNormalTestTimeOnX64),
      ],
      "C++": [
        (NORMAL, [],      [r"C\+\+:cException " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "IntegerDivideByZero": [
        (NORMAL, [],      [r"IntegerDivideByZero " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "IntegerOverflow": [
        (NORMAL, [],      [r"IntegerOverflow (9b1\.540|a3a\.80a) @ <binary>!fIntegerOverflow"], nExpectedNormalTestTimeOnX64),
      ],
      "Numbered": [
        (NORMAL, [0x41414141, 0x42424242], [r"0x41414141 " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "IllegalInstruction": [
        (NORMAL, [],      [r"IllegalInstruction (667\.540|cf3\.80a) @ <binary>!fIllegalInstruction"], nExpectedNormalTestTimeOnX64),
      ],
      "PrivilegedInstruction": [
        (NORMAL, [],      [r"PrivilegedInstruction (802\.540|df4\.80a) @ <binary>!fPrivilegedInstruction"], nExpectedNormalTestTimeOnX64),
      ],
      "StackExhaustion": [
        (NORMAL, [0x100], [r"StackExhaustion " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "RecursiveCall": [
        (FULL,   [ 1],    [r"RecursiveCall\(1\) (785|1ce) @ <binary>!fStackRecursionFunction1"],            nExpectedRecursiveTestTimeOnX64),
        (NORMAL, [ 2],    [r"RecursiveCall\(2\) (785\.923|1ce\.6b3) @ <binary>!fStackRecursionFunction1"],  nExpectedRecursiveTestTimeOnX64),
        (FULL,   [ 3],    [r"RecursiveCall\(3\) (785\.8a3|1ce\.f7f) @ <binary>!fStackRecursionFunction1"],  nExpectedRecursiveTestTimeOnX64),
        (FULL,   [20],    [r"RecursiveCall\(20\) (785\.0e0|1ce\.1ba) @ <binary>!fStackRecursionFunction1"], nExpectedRecursiveTestTimeOnX64),
      ],
      "PureCall": [
        # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
        # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
        # depends on the build of the application and whether symbols are being used.
        (NORMAL, [],      [r"PureCall (1b7\.a2a|640\.d7b) @ <binary>!fCallVirtual"], nExpectedNormalTestTimeOnX64),
      ],
      "WrongHeapHandle": [
        (NORMAL, [0x20],  [r"WrongHeap\[4n\] " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "OOM": [
        (NORMAL, ["HeapAlloc", mGlobals.uOOMAllocationBlockSize], [r"OOM " + srMain], nExpectedNormalTestTimeOnX64),
        (FULL,   ["C++", mGlobals.uOOMAllocationBlockSize],       [r"OOM " + srMain], nExpectedNormalTestTimeOnX64),
        (NORMAL, ["Stack", mGlobals.uOOMAllocationBlockSize],     [r"OOM " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "WRTOriginate": [
        (NORMAL, [0x87654321, "message"], [r"Stowed\[0x87654321\] " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "WRTLanguage": [
        (NORMAL, [0x87654321, "message"], [r"Stowed\[0x87654321:WRTLanguage@cIUnknown\] " + srMain], nExpectedNormalTestTimeOnX64),
      ],
      "CPUUsage": [
        (FULL, [], ["CPUUsage " + srMain], {"bExcessiveCPUUsageChecks": True}, cBugId.dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"] + nExpectedNormalTestTimeOnX64),
      ],
    };
    ###################################################
    from fAddDoubleFreeTests import fAddDoubleFreeTests;
    fAddDoubleFreeTests(dxTests, cBugId.dxConfig["uMaxMemoryDumpSize"]);
    from fAddMisalignedFreeTests import fAddMisalignedFreeTests;
    fAddMisalignedFreeTests(dxTests);
    from fAddOutOfBoundsTests import fAddOutOfBoundsTests;
    fAddOutOfBoundsTests(dxTests, mGlobals.uLargeHeapBlockSize);
    from fAddUseAfterFreeTests import fAddUseAfterFreeTests;
    fAddUseAfterFreeTests(dxTests);
    from fAddBufferOverrunTests import fAddBufferOverrunTests;
    fAddBufferOverrunTests(dxTests);
    from fAddAccessViolationTests import fAddAccessViolationTests;
    fAddAccessViolationTests(dxTests);
    from fAddSafeIntTests import fAddSafeIntTests;
    fAddSafeIntTests(dxTests);
    ###################################################
    def fatxProcessTests(xTests, asTestsSharedArguments = []):
      if isinstance(xTests, dict):
        dxTests = xTests;
        atxTests = [];
        for (sArgument, xSubTests) in dxTests.items():
          atxTests += fatxProcessTests(xSubTests, asTestsSharedArguments + [sArgument]);
      else:
        assert isinstance(xTests, list), \
            "Invalid test data %s" % repr(atxTests);
        atxTests = [];
        for txTest in xTests:
          assert isinstance(txTest, tuple) and len(txTest) in (4, 5), \
              "Invalid test data  %s" % repr(xTests);
          if len(txTest) == 4:
            (uTestLevel, axTestSpecificArguments, asrBugIds, nExpectedTestRunTime) = txTest;
            dxOptions = {};
          else:
            (uTestLevel, axTestSpecificArguments, asrBugIds, dxOptions, nExpectedTestRunTime) = txTest;
          for sISA in asTestISAs:
            if (
              uTestLevel == QUICK
              or (uTestLevel == NORMAL and not bTestQuick)
              or (uTestLevel == FULL and bTestFull)
              or (uTestLevel == x86 and sISA == "x86")
              or (uTestLevel == x64 and sISA == "x64")
              or (uTestLevel == FULL_x86 and bTestFull and sISA == "x86")
              or (uTestLevel == FULL_x64 and bTestFull and sISA == "x64")
            ):
              asTestArguments = asTestsSharedArguments + [
                x if isinstance(x, str) else
                ("%d" if x < 10 else "0x%X") % x
                for x in axTestSpecificArguments
              ] or [];
              atxTests.append((
                sISA,
                asTestArguments,
                asrBugIds,
                dxOptions,
                nExpectedTestRunTime + dnTestAdditionalExpectedRunTime_by_sISA[sISA]
              ));
      return atxTests;
    
    atxTests = fatxProcessTests(dxTests);
    uProgressCounter = 0;
    uNumberOfTests = len(atxTests);
    n0ExpectedMaximumTotalTestTimeInSeconds = 0;
    for (sISA, asTestArguments, asrBugIds, dxOptions, nExpectedMaximumTestTime) in atxTests:
        uProgressCounter += 1;
        oConsole.fProgressBar(
          uProgressCounter / len(atxTests),
          sISA, " ",
          " ".join(asTestArguments),
#          " ASan" if bASan else "",
          " (", str(uProgressCounter), " / ", str(len(atxTests)), ")",
        );
        n0ExpectedMaximumTotalTestTimeInSeconds += nExpectedMaximumTestTime;
        fRunASingleTest(
          sISA,
          asTestArguments,
          asrBugIds,
          bASan = False,
          bEnableVerboseOutput = bEnableVerboseOutput,
          n0ExpectedMaximumTestTime = nExpectedMaximumTestTime,
          **dxOptions,
        );
  nTotalTestTimeInSeconds = time.time() - nStartTimeInSeconds;
  if n0ExpectedMaximumTotalTestTimeInSeconds is not None and nTotalTestTimeInSeconds > n0ExpectedMaximumTotalTestTimeInSeconds:
    oConsole.fOutput(
      COLOR_WARN, "▲",
      COLOR_NORMAL, " Testing completed in %3.3f seconds, which is considered slow!" % nTotalTestTimeInSeconds,
    );
  else:
    oConsole.fOutput(
      COLOR_OK, "✓",
      COLOR_NORMAL, " Testing completed in %3.3f seconds" % nTotalTestTimeInSeconds,
    );
  nAverageTestTimePerTest = nTotalTestTimeInSeconds / uNumberOfTests;
  oConsole.fOutput("  The average test time was %f seconds." % nAverageTestTimePerTest);
except Exception as oException:
  if m0DebugOutput:
    m0DebugOutput.fTerminateWithException(oException, guExitCodeInternalError, bShowStacksForAllThread = True);
  raise;
