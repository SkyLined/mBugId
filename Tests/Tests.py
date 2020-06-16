import json, os, sys;

# Augment the search path to make the test subject a package and have access to its modules folder.
sTestsFolderPath = os.path.dirname(os.path.abspath(__file__));
sMainFolderPath = os.path.dirname(sTestsFolderPath);
sParentFolderPath = os.path.dirname(sMainFolderPath);
sModulesFolderPath = os.path.join(sMainFolderPath, "modules");
asOriginalSysPath = sys.path[:];
sys.path = [sParentFolderPath, sModulesFolderPath] + asOriginalSysPath;
# Load product details
oProductDetailsFile = open(os.path.join(sMainFolderPath, "dxProductDetails.json"), "rb");
try:
  dxProductDetails = json.load(oProductDetailsFile);
finally:
  oProductDetailsFile.close();
# Save the list of names of loaded modules:
asOriginalModuleNames = sys.modules.keys();

__import__(dxProductDetails["sProductName"], globals(), locals(), [], -1);

# Sub-packages should load all modules relative, or they will end up in the global namespace, which means they may get
# loaded by the script importing it if it tries to load a differnt module with the same name. Obviously, that script
# will probably not function when the wrong module is loaded, so we need to check that we did this correctly.
asUnexpectedModules = list(set([
  sModuleName.lstrip("_").split(".", 1)[0] for sModuleName in sys.modules.keys()
  if not (
    sModuleName in asOriginalModuleNames # This was loaded before
    or sModuleName.lstrip("_").split(".", 1)[0] in (
      [dxProductDetails["sProductName"]] +
      dxProductDetails["asDependentOnProductNames"] +
      [
        # This is optional, not required:
        "oConsole",
        # These built-in modules are expected:
        "base64", "binascii", "bz2", "calendar", "collections", "contextlib",
        "cStringIO", "ctypes", "datetime", "dis", "encodings", "fnmatch", "gc",
        "hashlib", "heapq", "hmac", "imp", "inspect", "io", "itertools",
        "json", "keyword", "math", "msvcrt", "nturl2path", "opcode",
        "platform", "shutil", "socket", "ssl", "string", "strop", "struct",
        "subprocess", "textwrap", "thread", "threading", "time", "token",
        "tokenize", "Queue", "urllib", "urlparse", "uuid", "winreg",
        "zipfile", "zlib",
      ]
    )
  )
]));
assert len(asUnexpectedModules) == 0, \
      "Module(s) %s was/were unexpectedly loaded!" % ", ".join(sorted(asUnexpectedModules));
for sModuleName in dxProductDetails["asDependentOnProductNames"]:
  assert sModuleName in sys.modules, \
      "%s is listed as a dependency but not loaded by the module!" % sModuleName;

from mDebugOutput import fEnableDebugOutputForModule, fTerminateWithException;
from oConsole import oConsole;
import os, platform, time;
nStartTimeInSeconds = time.clock();
try:
  #Import the test subject
  from cBugId import cBugId;
  from cBugId.mAccessViolation.fbUpdateReportForSpecialPointer import gddtsDetails_uSpecialAddress_sISA;
  import mFileSystem2;
  from mWindowsAPI import fsGetPythonISA;
  from mWindowsSDK import *;
  from fRunTest import fRunTest;
  from mGlobals import *;

  #from mDebugOutput import fShowFileDebugOutputForClass;
  #from mMultiThreading import cLock, cThread, cWithCallbacks;
  #fShowFileDebugOutputForClass(cLock);
  #fShowFileDebugOutputForClass(cThread);
  #fShowFileDebugOutputForClass(cWithCallbacks);

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

  sReportsFolderName = os.path.join(sTestsFolderPath, "Reports");

  bFailed = False;
  bTestQuick = False;
  bTestAll = False;
  sISA = None;
  asCommandLineArguments = [];
  for sArgument in sys.argv[1:]:
    if sArgument == "--all": 
      bTestQuick = False;
      bTestAll = True;
      gbGenerateReportHTML = True;
    elif sArgument in ["--report", "--reports"]: 
      gbGenerateReportHTML = True;
      gbSaveReportHTML = True;
    elif sArgument == "--quick": 
      bTestQuick = True;
      bTestAll = False;
    elif sArgument == "--show-cdb-io": 
      gbShowCdbIO = True;
    elif sArgument == "--debug": 
      fEnableDebugOutputForClass(cBugId);
    elif sISA is None:
      sISA = sArgument;
    else:
      asCommandLineArguments.append(sArgument);
  if len(asCommandLineArguments) > 0:
    gbShowApplicationIO = True;
    oConsole.fOutput("* Starting test...");
    fRunTest(
      sISA = sISA,
      axCommandLineArguments = asCommandLineArguments,
      asExpectedBugIdAndLocations = None, # Expect no exceptions.
      bExcessiveCPUUsageChecks = True,
    );
  else:
    assert sISA is None, \
        "Unknown argument %s" % sISA;
    oConsole.fOutput("* Starting tests...");
    if not bTestAll:
      # When we're not running the full test suite, we're not saving reports, so we don't need symbols.
      # Disabling symbols should speed things up considerably.
      cBugId.dxConfig["asDefaultSymbolServerURLs"] = None;
    # This will try to debug a non-existing application and check that the error thrown matches the expected value.
    fRunTest("x86",     None,                                                      [], \
        sApplicationBinaryPath = "<invalid>", \
        sExpectedFailedToDebugApplicationErrorMessage = "Unable to start a new process for binary \"<invalid>\".");
    fRunTest("x86",     None,                                                      [], \
        sApplicationBinaryPath = "does not exist", \
        sExpectedFailedToDebugApplicationErrorMessage = "Unable to start a new process for binary \"does not exist\".");
    for sISA in asTestISAs:
      fRunTest(sISA,    ["Nop"],                                                   []); # No exceptions, just a clean program exit.
      fRunTest(sISA,    ["Breakpoint"],                                            ["Breakpoint ed2.531 @ <test-binary>!wmain"]);
      if bTestQuick:
        continue; # Just do a test without a crash and breakpoint.
      # This will run the test in a cmd shell, so the exception happens in a child process. This should not affect the outcome.
      fRunTest(sISA,    ["Breakpoint"],                                            ["Breakpoint ed2.531 @ <test-binary>!wmain"],
          bRunInShell = True);
      fRunTest(sISA,    ["CPUUsage"],                                              ["CPUUsage ed2.531 @ <test-binary>!wmain"],
          bExcessiveCPUUsageChecks = True);
      fRunTest(sISA,    ["C++"],                                                   ["C++:cException ed2.531 @ <test-binary>!wmain"]);
      fRunTest(sISA,    ["IntegerDivideByZero"],                                   ["IntegerDivideByZero ed2.531 @ <test-binary>!wmain"]);
# This test will throw a first chance integer overflow, but Visual Studio added an exception Callback that then triggers
# another exception, so the report is incorrect.
#      fRunTest(sISA,    ["IntegerOverflow"],                                      "IntegerOverflow xxx.ed2");
      fRunTest(sISA,    ["Numbered", 0x41414141, 0x42424242],                      ["0x41414141 ed2.531 @ <test-binary>!wmain"]);
      fRunTest(sISA,    ["IllegalInstruction"],                                    ["*IllegalInstruction f17\.(f17|ed2) @ <test-binary>!fIllegalInstruction"]);
      fRunTest(sISA,    ["PrivilegedInstruction"],                                 ["*PrivilegedInstruction 0fc\.(0fc|ed2) @ <test-binary>!fPrivilegedInstruction"]);
      fRunTest(sISA,    ["StackExhaustion", 0x100],                                ["StackExhaustion ed2.531 @ <test-binary>!wmain"]);
      fRunTest(sISA,    ["RecursiveCall", 2],                                      ["RecursiveCall 950.6d1 @ <test-binary>!fStackRecursionFunction1"]);
      if bTestAll:
        fRunTest(sISA,  ["RecursiveCall", 1],                                      ["RecursiveCall 950 @ <test-binary>!fStackRecursionFunction1"]);
        fRunTest(sISA,  ["RecursiveCall", 3],                                      ["RecursiveCall 950.4e9 @ <test-binary>!fStackRecursionFunction1"]);
        fRunTest(sISA,  ["RecursiveCall", 20],                                     ["RecursiveCall 950.48b @ <test-binary>!fStackRecursionFunction1"]);
      # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
      # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
      # depends on the build of the application and whether symbols are being used.
      fRunTest(sISA,    ["PureCall"],                                              ["PureCall 12d.838 @ <test-binary>!fCallVirtual"]);
      fRunTest(sISA,    ["WrongHeapHandle", 0x20],                                 ["WrongHeap[4n] ed2.531 @ <test-binary>!wmain"]);
      fRunTest(sISA,    ["OOM", "HeapAlloc", guOOMAllocationBlockSize],            ["OOM ed2.531 @ <test-binary>!wmain"]);
      fRunTest(sISA,    ["OOM", "C++", guOOMAllocationBlockSize],                  ["OOM ed2.531 @ <test-binary>!wmain"]);
      fRunTest(sISA,    ["OOM", "Stack", guOOMAllocationBlockSize],                ["OOM ed2.531 @ <test-binary>!wmain"]);
      # WRT
      fRunTest(sISA,    ["WRTOriginate", 0x87654321, "message"],                   ["Stowed[0x87654321] ed2.531 @ <test-binary>!wmain"]);
      fRunTest(sISA,    ["WRTLanguage",  0x87654321, "message"],                   ["Stowed[0x87654321:WRTLanguage@cIUnknown] ed2.531 @ <test-binary>!wmain"]);
      # Double free
      fRunTest(sISA,    ["DoubleFree",                1],                          ["DoubleFree[1] ed2.531 @ <test-binary>!wmain"]);
      if bTestAll:
        fRunTest(sISA,  ["DoubleFree",                2],                          ["DoubleFree[2] ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["DoubleFree",                3],                          ["DoubleFree[3] ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["DoubleFree",                4],                          ["DoubleFree[4n] ed2.531 @ <test-binary>!wmain"]);
        # Extra tests to check if the code deals correctly with memory areas too large to dump completely:
        uMax = cBugId.dxConfig["uMaxMemoryDumpSize"];
        fRunTest(sISA,  ["DoubleFree",             uMax],                          ["DoubleFree[4n] ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["DoubleFree",         uMax + 1],                          ["DoubleFree[4n+1] ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["DoubleFree",         uMax + 4],                          ["DoubleFree[4n] ed2.531 @ <test-binary>!wmain"]);
        
      # Misaligned free
      fRunTest(sISA,    ["MisalignedFree",            1,  1],                      ["MisalignedFree[1]+0 ed2.531 @ <test-binary>!wmain"]);
      if bTestAll:
        fRunTest(sISA,  ["MisalignedFree",            1,  2],                      ["MisalignedFree[1]+1 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            2,  4],                      ["MisalignedFree[2]+2 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            3,  6],                      ["MisalignedFree[3]+3 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            4,  8],                      ["MisalignedFree[4n]+4n ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            5,  10],                     ["MisalignedFree[4n+1]+4n+1 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            2,  1],                      ["MisalignedFree[2]@1 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            3,  2],                      ["MisalignedFree[3]@2 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            4,  3],                      ["MisalignedFree[4n]@3 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            5,  4],                      ["MisalignedFree[4n+1]@4n ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            1,  -1],                     ["MisalignedFree[1]-1 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            1,  -2],                     ["MisalignedFree[1]-2 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            1,  -3],                     ["MisalignedFree[1]-3 ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            1,  -4],                     ["MisalignedFree[1]-4n ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["MisalignedFree",            1,  -5],                     ["MisalignedFree[1]-4n-1 ed2.531 @ <test-binary>!wmain"]);
      # NULL pointers
      fRunTest(sISA,    ["AccessViolation",   "Read",     1],                      ["AVR:NULL+1 30e.ed2 @ <test-binary>!fuReadByte"]);
      if bTestAll:
        fRunTest(sISA,  ["AccessViolation",   "Read", 2],                          ["AVR:NULL+2 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", 3],                          ["AVR:NULL+3 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", 4],                          ["AVR:NULL+4n 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", 5],                          ["AVR:NULL+4n+1 30e.ed2 @ <test-binary>!fuReadByte"]);
      uSignPadding = {"x86": 0, "x64": 0xFFFFFFFF00000000}[sISA];
      fRunTest(sISA,    ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFF],    ["AVR:NULL-1 30e.ed2 @ <test-binary>!fuReadByte"]);
      if bTestAll:
        fRunTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFE],    ["AVR:NULL-2 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFD],    ["AVR:NULL-3 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFC],    ["AVR:NULL-4n 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFB],    ["AVR:NULL-4n-1 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFA],    ["AVR:NULL-4n-2 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF9],    ["AVR:NULL-4n-3 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF8],    ["AVR:NULL-4n 30e.ed2 @ <test-binary>!fuReadByte"]);
      # Small out-of-bounds writes that do not go outside of the memory page and therefore do not cause access violations.
      # These are detected by Page Heap / Application Verifier when the memory is freed.
      # This means it is not reported in the `fWriteByte` function that does the writing, but in wmain that does the freeing.
      fRunTest(sISA,    ["OutOfBounds", "Heap", "Write", 1, -1, 1],                ["OOBW[1]{-1~1} ed2.531 @ <test-binary>!wmain"]);
      if bTestAll:
        fRunTest(sISA,  ["OutOfBounds", "Heap", "Write", 2, -2, 2],                ["OOBW[2]{-2~2} ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["OutOfBounds", "Heap", "Write", 3, -3, 3],                ["OOBW[3]{-3~3} ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["OutOfBounds", "Heap", "Write", 4, -4, 4],                ["OOBW[4n]{-4n~4n} ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["OutOfBounds", "Heap", "Write", 5, -5, 5],                ["OOBW[4n+1]{-4n-1~4n+1} ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,  ["OutOfBounds", "Heap", "Write", 1, -4, 5],                ["OOBW[1]{-4n~4n} ed2.531 @ <test-binary>!wmain"]); # Last byte written is within bounds!
        # Make sure very large allocations do not cause issues in cBugId
        fRunTest(sISA,  ["OutOfBounds", "Heap", "Write", guLargeHeapBlockSize, -4, 4], ["OOBW[4n]{-4n~4n} ed2.531 @ <test-binary>!wmain"]);
      # Use After Free
      fRunTest(sISA,    ["UseAfterFree", "Read",    1,  0],                        ["RAF[1]@0 30e.ed2 @ <test-binary>!fuReadByte"]);
      if bTestAll:
        fRunTest(sISA,  ["UseAfterFree", "Write",   2,  1],                        ["WAF[2]@1 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Read",    3,  2],                        ["RAF[3]@2 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Write",   4,  3],                        ["WAF[4n]@3 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Read",    5,  4],                        ["RAF[4n+1]@4n 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Write",   6,  5],                        ["WAF[4n+2]@4n+1 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Call",    8,  0],                        ["EAF[4n]@0 f47.ed2 @ <test-binary>!fCall"]);
        fRunTest(sISA,  ["UseAfterFree", "Jump",    8,  0],                        ["EAF[4n]@0 46f.ed2 @ <test-binary>!fJump"]);
      fRunTest(sISA,    ["UseAfterFree", "Read",    1,  1],                        ["OOBRAF[1]+0 30e.ed2 @ <test-binary>!fuReadByte"]);
      if bTestAll:
        fRunTest(sISA,  ["UseAfterFree", "Write",   2,  3],                        ["OOBWAF[2]+1 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Read",    3,  5],                        ["OOBRAF[3]+2 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Write",   4,  7],                        ["OOBWAF[4n]+3 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Read",    5,  9],                        ["OOBRAF[4n+1]+4n 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Write",   6, 11],                        ["OOBWAF[4n+2]+4n+1 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Read",    1, -1],                        ["OOBRAF[1]-1 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Write",   1, -2],                        ["OOBWAF[1]-2 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Read",    1, -3],                        ["OOBRAF[1]-3 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Write",   1, -4],                        ["OOBWAF[1]-4n 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Read",    1, -5],                        ["OOBRAF[1]-4n-1 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["UseAfterFree", "Call",    8,  8],                        ["OOBEAF[4n]+0 f47.ed2 @ <test-binary>!fCall"]);
        fRunTest(sISA,  ["UseAfterFree", "Jump",    8,  8],                        ["OOBEAF[4n]+0 46f.ed2 @ <test-binary>!fJump"]);
      # These issues are not detected until they cause an access violation. Heap blocks may be aligned up to 0x10 bytes.
      fRunTest(sISA,    ["BufferOverrun",   "Heap", "Read",   0xC, 5],             ["OOBR[4n]+4n 30e.ed2 @ <test-binary>!fuReadByte"]);
      if bTestAll:
        fRunTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xD, 5],             ["OOBR[4n+1]+3 30e.ed2 @ <test-binary>!fuReadByte", "OOBR[4n+1]+4n 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xE, 5],             ["OOBR[4n+2]+2 30e.ed2 @ <test-binary>!fuReadByte", "OOBR[4n+2]+3 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xF, 5],             ["OOBR[4n+3]+1 30e.ed2 @ <test-binary>!fuReadByte", "OOBR[4n+3]+2 30e.ed2 @ <test-binary>!fuReadByte"]);
      # These issues are detected when they cause an access violation, but earlier OOBWs took place that did not cause AVs.
      # This causes memory corruption, which is detected and reported in the bug id between curly braces.
      # This next test causes one AV, which is reported first. Then when collateral continues and the application
      # frees the memory, verifier.dll notices the corruption and reports it as well...
      fRunTest(sISA,    ["BufferOverrun",   "Heap", "Write",  0xC, 5],             ["BOF[4n]+4n{+0~4n} 630.ed2 @ <test-binary>!fWriteByte", "BOF[4n]{+0~4n} ed2.531 @ <test-binary>!wmain"]);
      if bTestAll:
        # These tests cause multiple AVs as the buffer overflow continues to write beyond the end of the buffer.
        # The first one is detect as a BOF, as the AV is sequential to the heap corruption in the heap block suffix.
        # The second AV is sequential to the first, but no longer to the heap corruption, so it is not detected as a BOF
        fRunTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xD, 5],             ["BOF[4n+1]+3{+0~3} 630.ed2 @ <test-binary>!fWriteByte", "OOBW[4n+1]+4n{+0~3} 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xE, 5],             ["BOF[4n+2]+2{+0~2} 630.ed2 @ <test-binary>!fWriteByte", "OOBW[4n+2]+3{+0~2} 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xF, 5],             ["BOF[4n+3]+1{+0~1} 630.ed2 @ <test-binary>!fWriteByte", "OOBW[4n+3]+2{+0~1} 630.ed2 @ <test-binary>!fWriteByte"]);
        # For this buffer overflow, there is no heap block suffix in which to detect corruption, so it cannot be
        # detected as a BOF.
        fRunTest(sISA,  ["BufferOverrun",   "Heap", "Write", 0x10, 5],             ["OOBW[4n]+0 630.ed2 @ <test-binary>!fWriteByte", "OOBW[4n]+1 630.ed2 @ <test-binary>!fWriteByte"]); # First byte writen causes AV; no data hash
      # Stack based heap overflows can cause an access violation if the run off the end of the stack, or a debugbreak
      # when they overwrite the stack cookie and the function returns. Finding out how much to write to overwrite the
      # stack cookie but not run off the end of the stack requires a bit of dark magic. I've only tested these values
      # on x64!
      uSmash = sISA == "x64" and 0x200 or 0x100;
      fRunTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, uSmash],        ["OOBW:Stack ed2.531 @ <test-binary>!wmain"]);
      # The OS does not allocate a guard page at the top of the stack. Subsequently, there may be a writable allocation
      # there, and a large enough stack overflow will write way past the end of the stack before causing an AV. This
      # causes a different BugId, so this test is not reliable at the moment.
      # TODO: Reimplement pagehap and add feature that adds guard pages to all virtual allocations, so stacks buffer
      # overflows are detected as soon as they read/write past the end of the stack.
      # fRunTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, 0x100000],     "AVW[Stack]+0 630.ed2 @ <test-binary>!fWriteByte");
      
      fRunTest(sISA,         ["AccessViolation", "Read", "Unallocated"],           ["AVR:Unallocated 30e.ed2 @ <test-binary>!fuReadByte"]);
      if bTestAll:
        fRunTest(sISA,       ["AccessViolation", "Read", "Reserved"],              ["AVR:Reserved[4n]@0 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,       ["AccessViolation", "Read", "NoAccess"],              ["AVR:NoAccess[4n]@0 30e.ed2 @ <test-binary>!fuReadByte"]);
        fRunTest(sISA,       ["AccessViolation", "Read", "Guard"],                 ["AVR:Guard[4n]@0 30e.ed2 @ <test-binary>!fuReadByte"]);
      
      fRunTest(sISA,         ["AccessViolation", "Write", "Reserved"],             ["AVW:Reserved[4n]@0 630.ed2 @ <test-binary>!fWriteByte"]);
      if bTestAll:
        fRunTest(sISA,       ["AccessViolation", "Write", "Unallocated"],          ["AVW:Unallocated 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,       ["AccessViolation", "Write", "NoAccess"],             ["AVW:NoAccess[4n]@0 630.ed2 @ <test-binary>!fWriteByte"]);
        fRunTest(sISA,       ["AccessViolation", "Write", "Guard"],                ["AVW:Guard[4n]@0 630.ed2 @ <test-binary>!fWriteByte"]);
      
      fRunTest(sISA,         ["AccessViolation", "Jump", "NoAccess"],              ["AVE:NoAccess[4n]@0 46f.ed2 @ <test-binary>!fJump"]);
      if bTestAll:
        fRunTest(sISA,       ["AccessViolation", "Jump", "Unallocated"],           ["AVE:Unallocated 46f.ed2 @ <test-binary>!fJump"]);
        fRunTest(sISA,       ["AccessViolation", "Jump", "Reserved"],              ["AVE:Reserved[4n]@0 46f.ed2 @ <test-binary>!fJump"]);
        if sISA == "x64": # For unknown reasons the stack is truncated. TODO: findout why and fix it.
          fRunTest(sISA,     ["AccessViolation", "Jump", "Guard"],                 ["AVE:Guard[4n]@0 ed2 @ <test-binary>!wmain"]);
        else:
          fRunTest(sISA,     ["AccessViolation", "Jump", "Guard"],                 ["AVE:Guard[4n]@0 ed2.531 @ <test-binary>!wmain"]);
      
      fRunTest(sISA,         ["AccessViolation", "Call", "Guard"],                 ["AVE:Guard[4n]@0 f47.ed2 @ <test-binary>!fCall"]);
      if bTestAll:
        fRunTest(sISA,       ["AccessViolation", "Call", "Unallocated"],           ["AVE:Unallocated f47.ed2 @ <test-binary>!fCall"]);
        fRunTest(sISA,       ["AccessViolation", "Call", "Reserved"],              ["AVE:Reserved[4n]@0 f47.ed2 @ <test-binary>!fCall"]);
        fRunTest(sISA,       ["AccessViolation", "Call", "NoAccess"],              ["AVE:NoAccess[4n]@0 f47.ed2 @ <test-binary>!fCall"]);
      
      if bTestAll:
        if sISA == "x64":
          # On x64, there are some limitations to exceptions occuring at addresses between the userland and kernelland
          # memory address ranges.
          for uBaseAddress in [0x7fffffff0000, 0x7fffffffffff, 0x800000000000, 0x8000000000000000]:
            fRunTest(sISA,   ["AccessViolation", "Read", uBaseAddress],            ["AVR:Invalid 30e.ed2 @ <test-binary>!fuReadByte"]);
            if uBaseAddress >= 0x800000000000 and uBaseAddress < 0xffff800000000000:
              fRunTest(sISA, ["AccessViolation", "Write", uBaseAddress],           ["AV?:Invalid 630.ed2 @ <test-binary>!fWriteByte"]);
            else:
              fRunTest(sISA, ["AccessViolation", "Write", uBaseAddress],           ["AVW:Invalid 630.ed2 @ <test-binary>!fWriteByte"]);
            fRunTest(sISA,   ["AccessViolation", "Jump", uBaseAddress],            ["AVE:Invalid 46f.ed2 @ <test-binary>!fJump"]);
            fRunTest(sISA,   ["AccessViolation", "Call", uBaseAddress],            ["AVE:Invalid f47.ed2 @ <test-binary>!fCall"]);
        
        for (uBaseAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in gddtsDetails_uSpecialAddress_sISA[sISA].items():
          if uBaseAddress < (1 << 32) or (sISA == "x64" and uBaseAddress < (1 << 47)):
            fRunTest(sISA,   ["AccessViolation", "Read", uBaseAddress],            ["AVR:%s 30e.ed2 @ <test-binary>!fuReadByte" % sAddressId]);
            if bTestAll:
              fRunTest(sISA, ["AccessViolation", "Write", uBaseAddress],           ["AVW:%s 630.ed2 @ <test-binary>!fWriteByte" % sAddressId]);
              fRunTest(sISA, ["AccessViolation", "Call", uBaseAddress],            ["AVE:%s f47.ed2 @ <test-binary>!fCall" % sAddressId]);
              fRunTest(sISA, ["AccessViolation", "Jump", uBaseAddress],            ["AVE:%s 46f.ed2 @ <test-binary>!fJump" % sAddressId]);
          elif sISA == "x64":
            fRunTest(sISA,   ["AccessViolation", "Read", uBaseAddress],            ["AVR:%s 30e.ed2 @ <test-binary>!fuReadByte" % sAddressId]);
            if bTestAll:
              fRunTest(sISA, ["AccessViolation", "Write", uBaseAddress],           ["AV?:%s 630.ed2 @ <test-binary>!fWriteByte" % sAddressId]);
              fRunTest(sISA, ["AccessViolation", "Call", uBaseAddress],            ["AVE:%s f47.ed2 @ <test-binary>!fCall" % sAddressId]);
              fRunTest(sISA, ["AccessViolation", "Jump", uBaseAddress],            ["AVE:%s 46f.ed2 @ <test-binary>!fJump" % sAddressId]);
      # SafeInt tests
      if not bTestAll:
        fRunTest(sISA,    ["SafeInt", "++", "signed", 64],                         ["IntegerOverflow ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,    ["SafeInt", "--", "unsigned", 32],                       ["IntegerOverflow ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,    ["SafeInt", "*",  "signed", 16],                         ["IntegerOverflow ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,    ["SafeInt", "truncate",  "signed", 8],                   ["IntegerTruncation ed2.531 @ <test-binary>!wmain"]);
        fRunTest(sISA,    ["SafeInt", "signedness",  "signed", 16],                ["IntegerTruncation ed2.531 @ <test-binary>!wmain"]);
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
                fRunTest(sISA,    ["SafeInt", sOperation, sSignedness, uBits],     ["%s ed2.531 @ <test-binary>!wmain" % sTypeId]);
  nTestTimeInSeconds = time.clock() - nStartTimeInSeconds;
  oConsole.fOutput("+ Testing completed in %3.3f seconds" % nTestTimeInSeconds);
  sys.exit(0);
except Exception as oException:
  nTestTimeInSeconds = time.clock() - nStartTimeInSeconds;
  oConsole.fOutput("- Testing failed after %3.3f seconds" % nTestTimeInSeconds);
  fTerminateWithException(oException);