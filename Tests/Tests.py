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
  from mBugId.mAccessViolation.fbUpdateReportForSpecialPointer import gddtsDetails_uSpecialAddress_sISA;
  from mWindowsAPI import fsGetPythonISA;
  from mWindowsSDK import *;
  from fShowHelp import fShowHelp;
  
  from fRunASingleTest import fRunASingleTest;
  import mGlobals;
  
  nStartTimeInSeconds = time.time();
  
  cBugId.dxConfig["bShowAllCdbCommandsInReport"] = True;
  cBugId.dxConfig["nExcessiveCPUUsageCheckIntervalInSeconds"] = 0.5; # Excessive CPU usage should be apparent within half a second.
  cBugId.dxConfig["uArchitectureIndependentBugIdBits"] = 32; # Test architecture independent bug ids
  
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
  asCommandLineArguments = [];
  for sArgument in sys.argv[1:]:
    if sArgument == "--full": 
      bTestQuick = False;
      bTestFull = True;
      mGlobals.bGenerateReportHTML = True;
    elif sArgument in ["--report", "--reports"]: 
      mGlobals.bGenerateReportHTML = True;
      mGlobals.bSaveReportHTML = True;
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
  
  if sISA is None:
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
    oConsole.fOutput("* Starting test...");
    fRunASingleTest(
      sISA = sISA,
      axCommandLineArguments = asCommandLineArguments,
      asExpectedBugIdAndLocations = None, # Expect no exceptions.
      bExcessiveCPUUsageChecks = True,
    );
  else:
    assert sISA is None, \
        "Unknown argument %s" % sISA;
    oConsole.fOutput("* Starting tests...");
    if not bTestFull:
      # When we're not running the full test suite, we're not saving reports, so we don't need symbols.
      # Disabling symbols should speed things up considerably.
      cBugId.dxConfig["asDefaultSymbolServerURLs"] = None;
    # This will try to debug a non-existing application and check that the error thrown matches the expected value.
    fRunASingleTest("x86",     None,                                                      [], \
        s0ApplicationBinaryPath = "<invalid>", \
        sExpectedFailedToDebugApplicationErrorMessage = "Unable to start a new process for binary path \"<invalid>\": Win32 error 0x7B (ERROR_INVALID_NAME).");
    fRunASingleTest("x86",     None,                                                      [], \
        s0ApplicationBinaryPath = "does not exist", \
        sExpectedFailedToDebugApplicationErrorMessage = "Unable to start a new process for binary path \"does not exist\": Win32 error 0x2 (ERROR_FILE_NOT_FOUND).");
    for sISA in asTestISAs:
      for bASan in (False,): # Set to (True, False) once we get ASan support working.
        fRunASingleTest(sISA,    ["Nop"],                                                   [], bASan = bASan); # No exceptions, just a clean program exit.
        fRunASingleTest(sISA,    ["Breakpoint"],                                            [r"Breakpoint (540|80a) @ <binary>!wmain"], bASan = bASan);
        # This will run the test in a cmd shell, so the exception happens in a child process. This should not affect the outcome.
        fRunASingleTest(sISA,    ["Breakpoint"],                                            [r"Breakpoint (540|80a) @ <binary>!wmain"],
            bRunInShell = True, bASan = bASan);
        if bTestQuick:
          continue; # Just do a test without a crash and breakpoint.
        fRunASingleTest(sISA,    ["C++"],                                                   [r"C\+\+:cException (540|80a) @ <binary>!wmain"], bASan = bASan);
        fRunASingleTest(sISA,    ["IntegerDivideByZero"],                                   [r"IntegerDivideByZero (540|80a) @ <binary>!wmain"], bASan = bASan);
  # This test will throw a first chance integer overflow, but Visual Studio added an exception Callback that then triggers
  # another exception, so the report is incorrect.
        fRunASingleTest(sISA,    ["IntegerOverflow"],                                       [r"IntegerOverflow (9b1\.540|a3a\.80a) @ <binary>!fIntegerOverflow"], bASan = bASan);
        fRunASingleTest(sISA,    ["Numbered", 0x41414141, 0x42424242],                      [r"0x41414141 (540|80a) @ <binary>!wmain"], bASan = bASan);
        fRunASingleTest(sISA,    ["IllegalInstruction"],                                    [r"IllegalInstruction (667\.540|cf3\.80a) @ <binary>!fIllegalInstruction"], bASan = bASan);
        fRunASingleTest(sISA,    ["PrivilegedInstruction"],                                 [r"PrivilegedInstruction (802\.540|df4\.80a) @ <binary>!fPrivilegedInstruction"], bASan = bASan);
        fRunASingleTest(sISA,    ["StackExhaustion", 0x100],                                [r"StackExhaustion (540|80a) @ <binary>!wmain"], bASan = bASan);
        fRunASingleTest(sISA,    ["RecursiveCall", 2],                                      [r"RecursiveCall\(2\) (785\.923|1ce\.6b3) @ <binary>!fStackRecursionFunction1"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["RecursiveCall", 1],                                      [r"RecursiveCall\(1\) (785|1ce) @ <binary>!fStackRecursionFunction1"], bASan = bASan);
          fRunASingleTest(sISA,  ["RecursiveCall", 3],                                      [r"RecursiveCall\(3\) (785\.8a3|1ce\.f7f) @ <binary>!fStackRecursionFunction1"], bASan = bASan);
          fRunASingleTest(sISA,  ["RecursiveCall", 20],                                     [r"RecursiveCall\(20\) (785\.0e0|1ce\.1ba) @ <binary>!fStackRecursionFunction1"], bASan = bASan);
        # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
        # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
        # depends on the build of the application and whether symbols are being used.
        fRunASingleTest(sISA,    ["PureCall"],                                              [r"PureCall (1b7\.a2a|640\.d7b) @ <binary>!fCallVirtual"], bASan = bASan);
        fRunASingleTest(sISA,    ["WrongHeapHandle", 0x20],                                 [r"WrongHeap\[4n\] (540|80a) @ <binary>!wmain"], bASan = bASan);
        fRunASingleTest(sISA,    ["OOM", "HeapAlloc", mGlobals.uOOMAllocationBlockSize],    [r"OOM (540|80a) @ <binary>!wmain"], bASan = bASan);
        fRunASingleTest(sISA,    ["OOM", "C++", mGlobals.uOOMAllocationBlockSize],          [r"OOM (540|80a) @ <binary>!wmain"], bASan = bASan);
        fRunASingleTest(sISA,    ["OOM", "Stack", mGlobals.uOOMAllocationBlockSize],        [r"OOM (540|80a) @ <binary>!wmain"], bASan = bASan);
        # WRT
        fRunASingleTest(sISA,    ["WRTOriginate", 0x87654321, "message"],                   [r"Stowed\[0x87654321\] (540|80a) @ <binary>!wmain"], bASan = bASan);
        fRunASingleTest(sISA,    ["WRTLanguage",  0x87654321, "message"],                   [r"Stowed\[0x87654321:WRTLanguage@cIUnknown\] (540|80a) @ <binary>!wmain"], bASan = bASan);
        # Double free
        fRunASingleTest(sISA,    ["DoubleFree",                1],                          [r"DoubleFree\[1\] (540|80a) @ <binary>!wmain"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["DoubleFree",                2],                          [r"DoubleFree\[2\] (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["DoubleFree",                3],                          [r"DoubleFree\[3\] (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["DoubleFree",                4],                          [r"DoubleFree\[4n\] (540|80a) @ <binary>!wmain"], bASan = bASan);
          # Extra tests to check if the code deals correctly with memory areas too large to dump completely:
          uMax = cBugId.dxConfig["uMaxMemoryDumpSize"];
          fRunASingleTest(sISA,  ["DoubleFree",             uMax],                          [r"DoubleFree\[(4n|\?)\] (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["DoubleFree",         uMax + 1],                          [r"DoubleFree\[(4n\+1|\?)\] (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["DoubleFree",         uMax + 4],                          [r"DoubleFree\[(4n|\?)\] (540|80a) @ <binary>!wmain"], bASan = bASan);
          
        # Misaligned free
        fRunASingleTest(sISA,    ["MisalignedFree",            1,  1],                      [r"MisalignedFree\[1\]\+0 (540|80a) @ <binary>!wmain"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["MisalignedFree",            1,  2],                      [r"MisalignedFree\[1\]\+1 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            2,  4],                      [r"MisalignedFree\[2\]\+2 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            3,  6],                      [r"MisalignedFree\[3\]\+3 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            4,  8],                      [r"MisalignedFree\[4n\]\+4n (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            5,  10],                     [r"MisalignedFree\[4n\+1\]\+4n\+1 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            2,  1],                      [r"MisalignedFree\[2\]@1 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            3,  2],                      [r"MisalignedFree\[3\]@2 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            4,  3],                      [r"MisalignedFree\[4n\]@3 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            5,  4],                      [r"MisalignedFree\[4n\+1\]@4n (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            1,  -1],                     [r"MisalignedFree\[1\]\-1 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            1,  -2],                     [r"MisalignedFree\[1\]\-2 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            1,  -3],                     [r"MisalignedFree\[1\]\-3 (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            1,  -4],                     [r"MisalignedFree\[1\]\-4n (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["MisalignedFree",            1,  -5],                     [r"MisalignedFree\[1\]\-4n\-1 (540|80a) @ <binary>!wmain"], bASan = bASan);
        # NULL pointerrs
        fRunASingleTest(sISA,    ["AccessViolation",   "Read", 1],                          [r"AVR:NULL\+1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", 2],                          [r"AVR:NULL\+2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", 3],                          [r"AVR:NULL\+3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", 4],                          [r"AVR:NULL\+4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", 5],                          [r"AVR:NULL\+4n\+1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        uSignPadding = {"x86": 0, "x64": 0xFFFFFFFF00000000}[sISA];
        fRunASingleTest(sISA,    ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFF],    [r"AVR:NULL\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFE],    [r"AVR:NULL\-2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFD],    [r"AVR:NULL\-3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFC],    [r"AVR:NULL\-4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFB],    [r"AVR:NULL\-4n\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFA],    [r"AVR:NULL\-4n\-2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF9],    [r"AVR:NULL\-4n\-3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF8],    [r"AVR:NULL\-4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        # Small out-of-bounds writes that do not go outside of the memory page and therefore do not cause access violations.
        # These are detected by Page Heap / Application Verifier when the memory is freed.
        # This means it is not reported in the `fWriteByte` function that does the writing, but in wmain that does the freeing.
        fRunASingleTest(sISA,    ["OutOfBounds", "Heap", "Write", 1, -1, 1],                [r"OOBW\[1\]\{\-1~1\} (540|80a) @ <binary>!wmain"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["OutOfBounds", "Heap", "Write", 2, -2, 2],                [r"OOBW\[2\]\{\-2~2\} (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["OutOfBounds", "Heap", "Write", 3, -3, 3],                [r"OOBW\[3\]\{\-3~3\} (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["OutOfBounds", "Heap", "Write", 4, -4, 4],                [r"OOBW\[4n\]\{\-4n~4n\} (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["OutOfBounds", "Heap", "Write", 5, -5, 5],                [r"OOBW\[4n\+1\]\{-4n\-1~4n\+1\} (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,  ["OutOfBounds", "Heap", "Write", 1, -4, 5],                [r"OOBW\[1\]\{\-4n~4n\} (540|80a) @ <binary>!wmain"], bASan = bASan); # Last byte written is within bounds!
          # Make sure very large allocations do not cause issues in cBugId
          fRunASingleTest(sISA,  ["OutOfBounds", "Heap", "Write", mGlobals.uLargeHeapBlockSize, -4, 4],
                                                                                            [r"OOBW\[4n\]\{\-4n~4n\} (540|80a) @ <binary>!wmain"], bASan = bASan);
        # Use After Free
        fRunASingleTest(sISA,    ["UseAfterFree", "Read",    1,  0],                        [r"RAF\[1\]@0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   2,  1],                        [r"WAF\[2\]@1 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Read",    3,  2],                        [r"RAF\[3\]@2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   4,  3],                        [r"WAF\[4n\]@3 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Read",    5,  4],                        [r"RAF\[4n\+1\]@4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   6,  5],                        [r"WAF\[4n\+2\]@4n\+1 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Call",    8,  0],                        [r"EAF\[4n\]@0 (b2d\.540|681\.80a) @ <binary>!fCall"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Jump",    8,  0],                        [r"EAF\[4n\]@0 (414\.540|fb0\.80a) @ <binary>!fJump"], bASan = bASan);
        fRunASingleTest(sISA,    ["UseAfterFree", "Read",    1,  1],                        [r"OOBRAF\[1\]\+0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   2,  3],                        [r"OOBWAF\[2\]\+1 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Read",    3,  5],                        [r"OOBRAF\[3\]\+2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   4,  7],                        [r"OOBWAF\[4n\]\+3 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Read",    5,  9],                        [r"OOBRAF\[4n\+1\]\+4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   6, 11],                        [r"OOBWAF\[4n\+2\]\+4n\+1 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Read",    1, -1],                        [r"OOBRAF\[1\]\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   1, -2],                        [r"OOBWAF\[1\]\-2 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Read",    1, -3],                        [r"OOBRAF\[1\]\-3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Write",   1, -4],                        [r"OOBWAF\[1\]\-4n (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Read",    1, -5],                        [r"OOBRAF\[1\]\-4n\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Call",    8,  8],                        [r"OOBEAF\[4n\]\+0 (b2d\.540|681\.80a) @ <binary>!fCall"], bASan = bASan);
          fRunASingleTest(sISA,  ["UseAfterFree", "Jump",    8,  8],                        [r"OOBEAF\[4n\]\+0 (414\.540|fb0\.80a) @ <binary>!fJump"], bASan = bASan);
        # These issues are not detected until they cause an access violation. Heap blocks may be aligned up to 0x10 bytes.
        fRunASingleTest(sISA,    ["BufferOverrun",   "Heap", "Read",   0xC, 5],             [r"OOBR\[4n\]\+4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xD, 5],             [r"OOBR\[4n\+1\]\+3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte", "OOBR\[4n\+1\]\+4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xE, 5],             [r"OOBR\[4n\+2\]\+2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte", "OOBR\[4n\+2\]\+3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xF, 5],             [r"OOBR\[4n\+3\]\+1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte", "OOBR\[4n\+3\]\+2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        # These issues are detected when they cause an access violation, but earlier OOBWs took place that did not cause AVs.
        # This causes memory corruption, which is detected and reported in the bug id between curly braces.
        # This next test causes one AV, which is reported first. Then when collateral continues and the application
        # frees the memory, verifier.dll notices the corruption and reports it as well...
        fRunASingleTest(sISA,    ["BufferOverrun",   "Heap", "Write",  0xC, 5],             [r"BOF\[4n\]\+4n\{\+0~4n\} (975\.540|113\.80a) @ <binary>!fWriteByte", "BOF\[4n\]\{\+0~4n\} (540|80a) @ <binary>!wmain"], bASan = bASan);
        if bTestFull:
          # These tests cause multiple AVs as the buffer overflow continues to write beyond the end of the buffer.
          # The first one is detect as a BOF, as the AV is sequential to the heap corruption in the heap block suffix.
          # The second AV is sequential to the first, but no longer to the heap corruption, so it is not detected as a BOF
          fRunASingleTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xD, 5],             [r"BOF\[4n\+1\]\+3\{\+0~3\} (975\.540|113\.80a) @ <binary>!fWriteByte", "OOBW\[4n\+1\]\+4n\{\+0~3\} (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xE, 5],             [r"BOF\[4n\+2\]\+2\{\+0~2\} (975\.540|113\.80a) @ <binary>!fWriteByte", "OOBW\[4n\+2\]\+3\{\+0~2\} (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xF, 5],             [r"BOF\[4n\+3\]\+1\{\+0~1\} (975\.540|113\.80a) @ <binary>!fWriteByte", "OOBW\[4n\+3\]\+2\{\+0~1\} (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          # For this buffer overflow, there is no heap block suffix in which to detect corruption, so it cannot be
          # detected as a BOF.
          fRunASingleTest(sISA,  ["BufferOverrun",   "Heap", "Write", 0x10, 5],             [r"OOBW\[4n\]\+0 (975\.540|113\.80a) @ <binary>!fWriteByte", "OOBW\[4n\]\+1 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan); # First byte writen causes AV; no data hash
        # Stack based heap overflows can cause an access violation if the run off the end of the stack, or a debugbreak
        # when they overwrite the stack cookie and the function returns. Finding out how much to write to overwrite the
        # stack cookie but not run off the end of the stack requires a bit of dark magic. I've only tested these values
        # on x64!
        uSmash = sISA == "x64" and 0x200 or 0x100;
        fRunASingleTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, uSmash],        [r"OOBW:Stack (540|80a) @ <binary>!wmain"], bASan = bASan);
        # The OS does not allocate a guard page at the top of the stack. Subsequently, there may be a writable allocation
        # there, and a large enough stack overflow will write way past the end of the stack before causing an AV. This
        # causes a different BugId, so this test is not reliable at the moment.
        # TODO: Reimplement pageheap and add feature that adds guard pages to all virtual allocations, so stacks buffer
        # overflows are detected as soon as they read/write past the end of the stack.
        # fRunASingleTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, 0x100000],     "AVW[Stack]+0 (975\.540|113\.80a) @ <binary>!fWriteByte", bASan = bASan);
        
        fRunASingleTest(sISA,         ["AccessViolation", "Read", "Unallocated"],           [r"AVR:Unallocated (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,       ["AccessViolation", "Read", "Reserved"],              [r"AVR:Reserved\[4n\]@0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,       ["AccessViolation", "Read", "NoAccess"],              [r"AVR:NoAccess\[4n\]@0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
          fRunASingleTest(sISA,       ["AccessViolation", "Read", "Guard"],                 [r"AVR:Guard\[4n\]@0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
        
        fRunASingleTest(sISA,         ["AccessViolation", "Write", "Reserved"],             [r"AVW:Reserved\[4n\]@0 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,       ["AccessViolation", "Write", "Unallocated"],          [r"AVW:Unallocated (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,       ["AccessViolation", "Write", "NoAccess"],             [r"AVW:NoAccess\[4n\]@0 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
          fRunASingleTest(sISA,       ["AccessViolation", "Write", "Guard"],                [r"AVW:Guard\[4n\]@0 (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
        
        fRunASingleTest(sISA,         ["AccessViolation", "Jump", "NoAccess"],              [r"AVE:NoAccess\[4n\]@0 (414\.540|fb0\.80a) @ <binary>!fJump"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,       ["AccessViolation", "Jump", "Unallocated"],           [r"AVE:Unallocated (414\.540|fb0\.80a) @ <binary>!fJump"], bASan = bASan);
          fRunASingleTest(sISA,       ["AccessViolation", "Jump", "Reserved"],              [r"AVE:Reserved\[4n\]@0 (414\.540|fb0\.80a) @ <binary>!fJump"], bASan = bASan);
          # For unknown reasons the stack differs between x86 and x64 and can even be truncated. TODO: findout why and fix it.
          fRunASingleTest(sISA,     ["AccessViolation", "Jump", "Guard"],                   [r"AVE:Guard\[4n\]@0 (414\.540|fb0\.80a) @ <binary>!fJump"], bASan = bASan);
        
        fRunASingleTest(sISA,         ["AccessViolation", "Call", "Guard"],                 [r"AVE:Guard\[4n\]@0 (b2d\.540|681\.80a) @ <binary>!fCall"], bASan = bASan);
        if bTestFull:
          fRunASingleTest(sISA,       ["AccessViolation", "Call", "Unallocated"],           [r"AVE:Unallocated (b2d\.540|681\.80a) @ <binary>!fCall"], bASan = bASan);
          fRunASingleTest(sISA,       ["AccessViolation", "Call", "Reserved"],              [r"AVE:Reserved\[4n\]@0 (b2d\.540|681\.80a) @ <binary>!fCall"], bASan = bASan);
          fRunASingleTest(sISA,       ["AccessViolation", "Call", "NoAccess"],              [r"AVE:NoAccess\[4n\]@0 (b2d\.540|681\.80a) @ <binary>!fCall"], bASan = bASan);
        
        if bTestFull:
          if sISA == "x64":
            # On x64, there are some limitations to exceptions occuring at addresses between the userland and kernelland
            # memory address ranges.
            for uBaseAddress in [0x7fffffff0000, 0x7fffffffffff, 0x800000000000, 0x8000000000000000]:
              fRunASingleTest(sISA,   ["AccessViolation", "Read", uBaseAddress],            [r"AVR:Invalid (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"], bASan = bASan);
              if uBaseAddress >= 0x800000000000 and uBaseAddress < 0xffff800000000000:
                fRunASingleTest(sISA, ["AccessViolation", "Write", uBaseAddress],           [r"AV\?:Invalid (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
              else:
                fRunASingleTest(sISA, ["AccessViolation", "Write", uBaseAddress],           [r"AVW:Invalid (975\.540|113\.80a) @ <binary>!fWriteByte"], bASan = bASan);
              fRunASingleTest(sISA,   ["AccessViolation", "Jump", uBaseAddress],            [r"AVE:Invalid (414\.540|fb0\.80a) @ <binary>!fJump"], bASan = bASan);
              fRunASingleTest(sISA,   ["AccessViolation", "Call", uBaseAddress],            [r"AVE:Invalid (b2d\.540|681\.80a) @ <binary>!fCall"], bASan = bASan);
          
          for (uBaseAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in gddtsDetails_uSpecialAddress_sISA[sISA].items():
            if uBaseAddress < (1 << 32) or (sISA == "x64" and uBaseAddress < (1 << 47)):
              fRunASingleTest(sISA,   ["AccessViolation", "Read", uBaseAddress],            [r"AVR:%s (3ae\.540|3f0\.80a) @ <binary>!fuReadByte" % sAddressId], bASan = bASan);
              if bTestFull:
                fRunASingleTest(sISA, ["AccessViolation", "Write", uBaseAddress],           [r"AVW:%s (975\.540|113\.80a) @ <binary>!fWriteByte" % sAddressId], bASan = bASan);
                fRunASingleTest(sISA, ["AccessViolation", "Call", uBaseAddress],            [r"AVE:%s (b2d\.540|681\.80a) @ <binary>!fCall" % sAddressId], bASan = bASan);
                fRunASingleTest(sISA, ["AccessViolation", "Jump", uBaseAddress],            [r"AVE:%s (414\.540|fb0\.80a) @ <binary>!fJump" % sAddressId], bASan = bASan);
            elif sISA == "x64":
              fRunASingleTest(sISA,   ["AccessViolation", "Read", uBaseAddress],            [r"AVR:%s (3ae\.540|3f0\.80a) @ <binary>!fuReadByte" % sAddressId], bASan = bASan);
              if bTestFull:
                fRunASingleTest(sISA, ["AccessViolation", "Write", uBaseAddress],           [r"AV\?:%s (975\.540|113\.80a) @ <binary>!fWriteByte" % sAddressId], bASan = bASan);
                fRunASingleTest(sISA, ["AccessViolation", "Call", uBaseAddress],            [r"AVE:%s (b2d\.540|681\.80a) @ <binary>!fCall" % sAddressId], bASan = bASan);
                fRunASingleTest(sISA, ["AccessViolation", "Jump", uBaseAddress],            [r"AVE:%s (414\.540|fb0\.80a) @ <binary>!fJump" % sAddressId], bASan = bASan);
        # SafeInt tests
        if not bTestFull:
          fRunASingleTest(sISA,    ["SafeInt", "++", "signed", 64],                         [r"IntegerOverflow (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,    ["SafeInt", "--", "unsigned", 32],                       [r"IntegerUnderflow (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,    ["SafeInt", "*",  "signed", 16],                         [r"IntegerTruncation (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,    ["SafeInt", "truncate",  "signed", 8],                   [r"IntegerTruncation (540|80a) @ <binary>!wmain"], bASan = bASan);
          fRunASingleTest(sISA,    ["SafeInt", "signedness",  "signed", 16],                [r"IntegerTruncation (540|80a) @ <binary>!wmain"], bASan = bASan);
        else:
          for (sOperation, sTypeId) in {
            "++": "IntegerOverflow",
            "--": "IntegerUnderflow",
            "*": "IntegerTruncation",
            "truncate": "IntegerTruncation",
            "signedness": "IntegerTruncation",
          }.items():
            for sSignedness in ["signed", "unsigned"]:
              for uBits in [8, 16, 32, 64]:
                if uBits != 64 and sOperation != "truncate":
                  fRunASingleTest(sISA,    ["SafeInt", sOperation, sSignedness, uBits],     ["%s (540|80a) @ <binary>!wmain" % sTypeId], bASan = bASan);
        # Run as last test because it takes a lot of time. Otherwise, while debugging issues in another test, we would be waiting on this
        # test every time.
        fRunASingleTest(sISA,    ["CPUUsage"],                                              ["CPUUsage (540|80a) @ <binary>!wmain"],
            bExcessiveCPUUsageChecks = True, bASan = bASan);
  nTestTimeInSeconds = time.time() - nStartTimeInSeconds;
  oConsole.fOutput("+ Testing completed in %3.3f seconds" % nTestTimeInSeconds);
except Exception as oException:
  if m0DebugOutput:
    m0DebugOutput.fTerminateWithException(oException, guExitCodeInternalError, bShowStacksForAllThread = True);
  raise;
