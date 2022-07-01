import os, sys;
sModulePath = os.path.dirname(__file__);
sys.path = [sModulePath] + [sPath for sPath in sys.path if sPath.lower() != sModulePath.lower()];

from fTestDependencies import fTestDependencies;
fTestDependencies();

try: # mDebugOutput use is Optional
  import mDebugOutput as m0DebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  m0DebugOutput = None;

guExitCodeInternalError = 1; # Use standard value;
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
  asTestISAs = {
    "x86": ["x86"],
    "x64": ["x64", "x86"],
  }[sPythonISA];
  
  bFailed = False;
  bTestQuick = False;
  bTestFull = False;
  sISA = None;
  bEnableDebugOutput = False;
  bEnableVerboseOutput = False;
  asCommandLineArguments = [];
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
    elif sArgument == "--show-cdb-io": 
      mGlobals.bShowCdbIO = True;
    elif sArgument == "--debug": 
      bEnableDebugOutput = True;
    elif sArgument in ["-?", "/?", "/h", "-h", "--help"]: 
      fShowHelp(oConsole);
      sys.exit(0);
    elif sISA is None:
      sISA = sArgument;
    else:
      asCommandLineArguments.append(sArgument);
  
  if sISA is not None:
    oConsole.fOutput("+ ISA = %s." % sISA);
  if bTestQuick:
    oConsole.fOutput("+ Running quick tests.");
  elif bTestFull:
    oConsole.fOutput("+ Running full tests.");
  if mGlobals.bShowCdbIO:
    oConsole.fOutput("+ Showing cdb I/O.");
  if bEnableDebugOutput:
    assert m0DebugOutput, \
        "The 'mDebugOutput' moduke is needed to show debug output.";
    m0DebugOutput.fEnableAllDebugOutput();
    oConsole.fOutput("+ Showing debug output.");
  
  if len(asCommandLineArguments) > 0:
    mGlobals.bShowApplicationIO = True;
    fRunASingleTest(
      sISA = sISA,
      axCommandLineArguments = asCommandLineArguments,
      a0sExpectedBugIdAndLocations = None, # Expect no exceptions.
      s0ExpectedFailedToDebugApplicationErrorMessage = None,
      bRunInShell = False,
      s0ApplicationBinaryPath = None,
      bASan = False,
      uMaximumNumberOfBugs = 2,
      bExcessiveCPUUsageChecks = True,
      bEnableVerboseOutput = bEnableVerboseOutput,
    );
  else:
    assert sISA is None, \
        "Unknown argument %s" % sISA;
    if not bTestFull:
      # When we're not running the full test suite, we're not saving reports, so we don't need symbols.
      # Disabling symbols should speed things up considerably.
      cBugId.dxConfig["asDefaultSymbolServerURLs"] = None;
    dxTests = {
      "BinaryIssues": [
        (FULL, [], [], {
          "s0ApplicationBinaryPath": "<invalid>",
          "s0ExpectedFailedToDebugApplicationErrorMessage": \
              "Unable to start a new process for binary path \"<invalid>\": Win32 error 0x7B (ERROR_INVALID_NAME)."
        }),
        (FULL, [], [], {
          "s0ApplicationBinaryPath": "does not exist",
          "s0ExpectedFailedToDebugApplicationErrorMessage": \
              "Unable to start a new process for binary path \"does not exist\": Win32 error 0x2 (ERROR_FILE_NOT_FOUND).",
        }),
      ],
      "Breakpoint": [
        (QUICK, [], [r"Breakpoint (540|80a) @ <binary>!wmain"], {"bRunInShell": bTestFull}),
      ],
      "Nop": [
        (FULL, [], []), # No exceptions, just a clean program exit.
      ],
      "C++": [
        (NORMAL, [], [r"C\+\+:cException (540|80a) @ <binary>!wmain"]),
      ],
      "IntegerDivideByZero": [
        (NORMAL, [], [r"IntegerDivideByZero (540|80a) @ <binary>!wmain"]),
      ],
      "IntegerOverflow": [
        (NORMAL, [], [r"IntegerOverflow (9b1\.540|a3a\.80a) @ <binary>!fIntegerOverflow"]),
      ],
      "Numbered": [
        (NORMAL, [0x41414141, 0x42424242], [r"0x41414141 (540|80a) @ <binary>!wmain"]),
      ],
      "IllegalInstruction": [
        (NORMAL, [], [r"IllegalInstruction (667\.540|cf3\.80a) @ <binary>!fIllegalInstruction"]),
      ],
      "PrivilegedInstruction": [
        (NORMAL, [], [r"PrivilegedInstruction (802\.540|df4\.80a) @ <binary>!fPrivilegedInstruction"]),
      ],
      "StackExhaustion": [
        (NORMAL, [0x100], [r"StackExhaustion (540|80a) @ <binary>!wmain"]),
      ],
      "RecursiveCall": [
        (FULL,   [ 1], [r"RecursiveCall\(1\) (785|1ce) @ <binary>!fStackRecursionFunction1"]),
        (NORMAL, [ 2], [r"RecursiveCall\(2\) (785\.923|1ce\.6b3) @ <binary>!fStackRecursionFunction1"]),
        (FULL,   [ 3], [r"RecursiveCall\(3\) (785\.8a3|1ce\.f7f) @ <binary>!fStackRecursionFunction1"]),
        (FULL,   [20], [r"RecursiveCall\(20\) (785\.0e0|1ce\.1ba) @ <binary>!fStackRecursionFunction1"]),
      ],
      "PureCall": [
        # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
        # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
        # depends on the build of the application and whether symbols are being used.
        (NORMAL, [], [r"PureCall (1b7\.a2a|640\.d7b) @ <binary>!fCallVirtual"]),
      ],
      "WrongHeapHandle": [
        (NORMAL, [0x20], [r"WrongHeap\[4n\] (540|80a) @ <binary>!wmain"]),
      ],
      "OOM": [
        (NORMAL, ["HeapAlloc", mGlobals.uOOMAllocationBlockSize], [r"OOM (540|80a) @ <binary>!wmain"]),
        (FULL,   ["C++", mGlobals.uOOMAllocationBlockSize],       [r"OOM (540|80a) @ <binary>!wmain"]),
        (NORMAL, ["Stack", mGlobals.uOOMAllocationBlockSize],     [r"OOM (540|80a) @ <binary>!wmain"]),
      ],
      "WRTOriginate": [
        (NORMAL, [0x87654321, "message"], [r"Stowed\[0x87654321\] (540|80a) @ <binary>!wmain"]),
      ],
      "WRTLanguage": [
        (NORMAL, [0x87654321, "message"], [r"Stowed\[0x87654321:WRTLanguage@cIUnknown\] (540|80a) @ <binary>!wmain"]),
      ],
      "CPUUsage": [
        (FULL, [], ["CPUUsage (540|80a) @ <binary>!wmain"], {"bExcessiveCPUUsageChecks": True}),
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
          assert isinstance(txTest, tuple) and len(txTest) in (3, 4), \
              "Invalid test data  %s" % repr(xTests);
          if len(txTest) == 3:
            (uTestLevel, axTestSpecificArguments, asrBugIds) = txTest;
            dxOptions = {};
          else:
            (uTestLevel, axTestSpecificArguments, asrBugIds, dxOptions) = txTest;
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
              atxTests.append((sISA, asTestArguments, asrBugIds, dxOptions));
      return atxTests;
    
    atxTests = fatxProcessTests(dxTests);
    uProgressCounter = 0;
    uNumberOfTests = len(atxTests); 
    for (sISA, asTestArguments, asrBugIds, dxOptions) in atxTests:
        uProgressCounter += 1;
        oConsole.fProgressBar(
          uProgressCounter / len(atxTests),
          sISA, " ",
          " ".join(asTestArguments),
#          " ASan" if bASan else "",
          " (", str(uProgressCounter), " / ", str(len(atxTests)), ")",
        );
        fRunASingleTest(
          sISA,
          asTestArguments,
          asrBugIds,
          bASan = False,
          bEnableVerboseOutput = bEnableVerboseOutput,
          **dxOptions,
        );
  nTestTimeInSeconds = time.time() - nStartTimeInSeconds;
  oConsole.fOutput("+ Testing completed in %3.3f seconds" % nTestTimeInSeconds);
except Exception as oException:
  if m0DebugOutput:
    m0DebugOutput.fTerminateWithException(oException, guExitCodeInternalError, bShowStacksForAllThread = True);
  raise;
