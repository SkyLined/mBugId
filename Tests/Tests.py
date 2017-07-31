import os, re, sys, threading, time, traceback;
sTestsFolderPath = os.path.dirname(os.path.abspath(__file__));
sBugIdFolderPath = os.path.dirname(sTestsFolderPath);
sBaseFolderPath = os.path.dirname(sBugIdFolderPath);
sys.path.extend([
  sBaseFolderPath,
  sBugIdFolderPath,
  os.path.join(sBugIdFolderPath, "modules"),
]);

bDebugStartFinish = False;  # Show some output when a test starts and finishes.
gbDebugIO = False;           # Show cdb I/O during tests (you'll want to run only 1 test at a time for this).

from cBugId import cBugId;
from cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION import ddtsDetails_uSpecialAddress_sISA;
from FileSystem import FileSystem;
from sOSISA import sOSISA;
cBugId.dxConfig["bShowAllCdbCommandsInReport"] = True;
cBugId.dxConfig["nExcessiveCPUUsageCheckInterval"] = 10; # The test application is simple: CPU usage should be apparent after a few seconds.
cBugId.dxConfig["uReserveRAM"] = 1024; # Simply test if reserving RAM works, not actually reserve any useful amount.
cBugId.dxConfig["uArchitectureIndependentBugIdBits"] = 32; # Test architecture independent bug ids

asTestISAs = [sOSISA];
if sOSISA == "x64":
  asTestISAs.append("x86");

sReportsFolderName = FileSystem.fsPath(sBugIdFolderPath, "Tests", "Reports");

dsBinaries_by_sISA = {
  "x86": os.path.join(sTestsFolderPath, r"bin\Tests_x86.exe"),
  "x64": os.path.join(sTestsFolderPath, r"bin\Tests_x64.exe"),
  "fail": os.path.join(sTestsFolderPath, r"bin\Binary_does_not_exist.exe"),
};

bFailed = False;
oOutputLock = threading.Lock();

class cTest(object):
  def __init__(oTest, sISA, axCommandLineArguments, sExpectedBugId, sExpectedFailedToDebugApplicationErrorMessage = None):
    oTest.sISA = sISA;
    oTest.asCommandLineArguments = axCommandLineArguments and [
      isinstance(x, str) and x
               or x < 10 and ("%d" % x)
                          or ("0x%X" % x)
      for x in axCommandLineArguments
    ] or [];
    oTest.sBinary = axCommandLineArguments is None and "<invalid>" or dsBinaries_by_sISA[oTest.sISA];
    oTest.bRunInShell = isinstance(axCommandLineArguments, tuple);
    oTest.sExpectedBugId = sExpectedBugId; # Can also be a tuple of valid values (e.g. PureCall/AppExit)
    oTest.sExpectedFailedToDebugApplicationErrorMessage = sExpectedFailedToDebugApplicationErrorMessage;
    oTest.sFailedToDebugApplicationErrorMessage = None;
    oTest.bHasOutputLock = False;
    oTest.bGenerateReportHTML = True;
    oTest.fErrorCallback = None;
  
  def __str__(oTest):
    if oTest.sExpectedFailedToDebugApplicationErrorMessage:
      return "%s => %s" % ("Running <invalid>", repr(oTest.sExpectedFailedToDebugApplicationErrorMessage));
    return "%s on %s%s => %s" % (" ".join(oTest.asCommandLineArguments), oTest.sISA, oTest.bRunInShell and " (in child process)" or "", repr(oTest.sExpectedBugId));
  
  def fOutputStdIn(oTest, oBugid, sInput):
    oOutputLock and oOutputLock.acquire();
    oTest.bHasOutputLock = True;
    print "<stdin<%s" % sInput;
    oOutputLock and oOutputLock.release();
    oTest.bHasOutputLock = False;  

  def fOutputStdOut(oTest, oBugid, sOutput):
    oOutputLock and oOutputLock.acquire();
    oTest.bHasOutputLock = True;
    print "stdout>%s" % sOutput;
    oOutputLock and oOutputLock.release();
    oTest.bHasOutputLock = False;  

  def fOutputStdErr(oTest, oBugid, sOutput):
    oOutputLock and oOutputLock.acquire();
    oTest.bHasOutputLock = True;
    print "stderr>%s" % sOutput;
    oOutputLock and oOutputLock.release();
    oTest.bHasOutputLock = False;  

  def fRun(oTest, fErrorCallback):
    global bFailed, oOutputLock;
    oTest.fErrorCallback = fErrorCallback;
    oOutputLock and oOutputLock.acquire();
    oTest.bHasOutputLock = True;
    print "* %s\r" % oTest,;
    oOutputLock and oOutputLock.release();
    oTest.bHasOutputLock = False;
    sApplicationBinaryPath = oTest.sBinary;
    asApplicationArguments = oTest.asCommandLineArguments;
    if oTest.bRunInShell:
      asApplicationArguments = ["/C", sApplicationBinaryPath] + asApplicationArguments; 
      sApplicationBinaryPath = os.environ.get("ComSpec");
    if bDebugStartFinish:
      oOutputLock and oOutputLock.acquire();
      oTest.bHasOutputLock = True;
      print "* Started %s" % oTest;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
    try:
      oTest.oBugId = cBugId(
        sCdbISA = oTest.sISA,
        sApplicationBinaryPath = sApplicationBinaryPath,
        asApplicationArguments = asApplicationArguments,
        asSymbolServerURLs = ["http://msdl.microsoft.com/download/symbols"], # Will be ignore if symbols are disabled.
        bGenerateReportHTML = oTest.bGenerateReportHTML,
        fFinishedCallback = oTest.fFinishedHandler,
        fInternalExceptionCallback = oTest.fInternalExceptionHandler,
        fFailedToDebugApplicationCallback = oTest.fFailedToDebugApplicationHandler,
        fPageHeapNotEnabledCallback = oTest.fPageHeapNotEnabledHandler,
        fStdInInputCallback = gbDebugIO and oTest.fOutputStdIn,
        fStdOutOutputCallback = gbDebugIO and oTest.fOutputStdOut,
        fStdErrOutputCallback = gbDebugIO and oTest.fOutputStdErr,
      );
      oTest.oBugId.fStart();
      oTest.oBugId.fSetCheckForExcessiveCPUUsageTimeout(1);
      oTest.oBugId.fWait();
    except Exception, oException:
      if not bFailed:
        bFailed = True;
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
        print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
        print "  Expected:    %s" % repr(oTest.sExpectedBugId);
        print "  Exception:   %s" % repr(oException);
        oOutputLock and oOutputLock.release();
        oTest.bHasOutputLock = False;
        fErrorCallback();
        raise;
  
  def fStop(oTest):
    hasattr(oTest, "oBugId") and oTest.oBugId.fStop();
  
  def fFinished(oTest):
    if bDebugStartFinish:
      oOutputLock and oOutputLock.acquire();
      oTest.bHasOutputLock = True;
      print "* Finished %s" % oTest;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
  
  def fFinishedHandler(oTest, oBugId, oBugReport):
    global bFailed, oOutputLock;
    try:
      if not bFailed:
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
        bThisTestFailed = False;
        if oTest.sExpectedFailedToDebugApplicationErrorMessage:
          if oTest.sFailedToDebugApplicationErrorMessage != oTest.sExpectedFailedToDebugApplicationErrorMessage:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test should have reported a failure to debug the application.";
            print "  Expected:    %s" % repr(oTest.sExpectedFailedToDebugApplicationErrorMessage);
            print "  Reported:    %s" % repr(oTest.sFailedToDebugApplicationErrorMessage);
            bThisTestFailed = True;
          else:
            print "+ %s" % oTest;
        elif oTest.sFailedToDebugApplicationErrorMessage:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test was unabled to debug the application:";
            print "  Expected:    no error";
            print "  Reported:    %s" % repr(oTest.sFailedToDebugApplicationErrorMessage);
        elif oTest.sExpectedBugId:
          if not oBugReport:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test should have reported a bug in the application.";
            print "  Expected:    %s" % repr(oTest.sExpectedBugId);
            print "  Reported:    no bug";
            bThisTestFailed = True;
          elif (
            (isinstance(oTest.sExpectedBugId, tuple) and oBugReport.sId in oTest.sExpectedBugId)
            or (isinstance(oTest.sExpectedBugId, str) and oBugReport.sId == oTest.sExpectedBugId)
          ):
            print "+ %s" % oTest;
          else:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test reported a different bug than expected in the application.";
            print "  Expected:    %s" % repr(oTest.sExpectedBugId);
            print "  Reported:    %s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
            print "               %s" % (oBugReport.sBugDescription);
            bThisTestFailed = True;
        elif oBugReport:
          print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
          print "  Test reported an unexpected bug in the application.";
          print "  Expected:    no bug";
          print "  Reported:    %s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
          print "               %s" % (oBugReport.sBugDescription);
          bThisTestFailed = True;
        else:
          print "+ %s == None" % oTest;
        if gbDebugIO:
          print;
          print "=" * 80;
          print;
        bFailed = bThisTestFailed;
        if bThisTestFailed:
          oTest.fErrorCallback();
        oOutputLock and oOutputLock.release();
        oTest.bHasOutputLock = False;
      if oTest.bGenerateReportHTML and oBugReport:
        # We'd like a report file name base on the BugId, but the later may contain characters that are not valid in a file name
        sDesiredReportFileName = "%s == %s @ %s.html" % (" ".join(oTest.asCommandLineArguments), oBugReport.sId, oBugReport.sBugLocation);
        # Thus, we need to translate these characters to create a valid filename that looks very similar to the BugId
        sValidReportFileName = FileSystem.fsValidName(sDesiredReportFileName, bUnicode = False);
        FileSystem.fWriteDataToFile(
          oBugReport.sReportHTML,
          sReportsFolderName,
          sValidReportFileName,
          fbRetryOnFailure = lambda: False,
        );
    finally:
      oTest.fFinished();
      oTest.bHandlingResult = False;
  
  def fInternalExceptionHandler(oTest, oBugId, oException, oTraceBack):
    global bFailed;
    oTest.fFinished();
    if not bFailed:
      # Exception in fFinishedHandler can cause this function to be executed with lock still in place.
      if not oTest.bHasOutputLock:
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
      bFailed = True;
      print "@" * 80;
      print "- An internal exception has occured in test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
      print "  %s" % repr(oException);
      print "  Stack:";
      txStack = traceback.extract_tb(oTraceBack);
      uFrameIndex = len(txStack) - 1;
      for (sFileName, uLineNumber, sFunctionName, sCode) in reversed(txStack):
        sSource = "%s/%d" % (sFileName, uLineNumber);
        if sFunctionName != "<module>":
          sSource = "%s (%s)" % (sFunctionName, sSource);
        print "  %3d %s" % (uFrameIndex, sSource);
        if sCode:
          print "      > %s" % sCode.strip();
        uFrameIndex -= 1;
      print "@" * 80;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
      oTest.fErrorCallback();
      raise;
  
  def fFailedToDebugApplicationHandler(oTest, oBugId, sErrorMessage):
    oTest.sFailedToDebugApplicationErrorMessage = sErrorMessage;

  def fPageHeapNotEnabledHandler(oTest, oBugId, uProcessId, sBinaryName, bPreventable):
    assert sBinaryName == "cmd.exe", \
        "It appears you have not enabled page heap for %s, which is required to run tests." % sBinaryName;

if __name__ == "__main__":
  aoTests = [];
  asArgs = sys.argv[1:];
  bQuickTestSuite = False;
  bFullTestSuite = False;
  bGenerateReportHTML = False;
  while asArgs:
    if asArgs[0] == "--full": 
      bFullTestSuite = True;
      bGenerateReportHTML = True;
    elif asArgs[0] == "--quick": 
      bQuickTestSuite = True;
    elif asArgs[0] == "--debug": 
      gbDebugIO = True;
      bGenerateReportHTML = True;
    else:
      break;
    asArgs.pop(0);
  if asArgs:
    gbDebugIO = True; # Single test: output stdio
    bGenerateReportHTML = True;
  if asArgs:
    aoTests.append(cTest(asArgs[0], asArgs[1:], None)); # Expect no exceptions.
  else:
    if not bFullTestSuite:
      # When we're not running the full test suite, we're not saving reports, so we don't need symbols.
      # Disabling symbols should speed things up considerably.
      cBugId.dxConfig["asDefaultSymbolServerURLs"] = None;
    # This will try to debug a non-existing application and check that the error thrown matches the expected value.
    aoTests.append(cTest("x86",     None,                                                     None, \
        'Failed to start application "<invalid>": Win32 error 0n2!\r\n- You may have provided an incorrect path to the executable.'));
    for sISA in asTestISAs:
      aoTests.append(cTest(sISA,    ["Nop"],                                                  None)); # No exceptions, just a clean program exit.
      aoTests.append(cTest(sISA,    ["Breakpoint"],                                           "Breakpoint ed2.531"));
      if bQuickTestSuite:
        continue; # Just do a test without a crash and breakpoint.
      # This will run the test in a cmd shell, so the exception happens in a child process. This should not affect the outcome.
      aoTests.append(cTest(sISA,    ("Breakpoint",),                                          "Breakpoint ed2.531"));
      aoTests.append(cTest(sISA,    ["CPUUsage"],                                             "CPUUsage ed2.531"));
      aoTests.append(cTest(sISA,    ["C++"],                                                 ("C++ ed2.531", "C++:cException ed2.531")));
      aoTests.append(cTest(sISA,    ["IntegerDivideByZero"],                                  "IntegerDivideByZero ed2.531"));
# This test will throw a first chance integer overflow, but Visual Studio added an exception handler that then triggers
# another exception, so the report is incorrect.
#      aoTests.append(cTest(sISA,    ["IntegerOverflow"],                                      "IntegerOverflow xxx.ed2"));
      aoTests.append(cTest(sISA,    ["Numbered", 0x41414141, 0x42424242],                     "0x41414141 ed2.531"));
      aoTests.append(cTest(sISA,    ["IllegalInstruction"],                                  ("IllegalInstruction f17.f17", "IllegalInstruction f17.ed2")));
      aoTests.append(cTest(sISA,    ["PrivilegedInstruction"],                               ("PrivilegedInstruction 0fc.0fc", "PrivilegedInstruction 0fc.ed2")));
      aoTests.append(cTest(sISA,    ["StackExhaustion", 0x100],                               "StackExhaustion ed2.531"));
      aoTests.append(cTest(sISA,    ["RecursiveCall", 2],                                     "RecursiveCall 950.6d1"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["RecursiveCall", 1],                                     "RecursiveCall 950"));
        aoTests.append(cTest(sISA,  ["RecursiveCall", 3],                                     "RecursiveCall 950.c9e"));
        aoTests.append(cTest(sISA,  ["RecursiveCall", 20],                                    "RecursiveCall 950.729"));
      # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
      # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
      # depends on the build of the application and whether symbols are being used.
      aoTests.append(cTest(sISA,    ["PureCall"],                                             "PureCall 12d.838"));
      uTooMuchRam = sISA == "x64" and 0x100000000000 or 0xC0000000;
      aoTests.append(cTest(sISA,    ["OOM", "HeapAlloc", uTooMuchRam],                        "OOM ed2.531"));
      aoTests.append(cTest(sISA,    ["OOM", "C++", uTooMuchRam],                              "OOM ed2.531"));
      # WRT
      aoTests.append(cTest(sISA,    ["WRTOriginate", "0x87654321", "message"],                "Stowed[0x87654321] ed2.531"));
      aoTests.append(cTest(sISA,    ["WRTLanguage",  "0x87654321", "message"],                "Stowed[0x87654321@cIUnknown] ed2.531"));
      # Double free
      aoTests.append(cTest(sISA,    ["DoubleFree",                1],                         "DoubleFree[1] ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["DoubleFree",                2],                         "DoubleFree[2] ed2.531"));
        aoTests.append(cTest(sISA,  ["DoubleFree",                3],                         "DoubleFree[3] ed2.531"));
        aoTests.append(cTest(sISA,  ["DoubleFree",                4],                         "DoubleFree[4n] ed2.531"));
        # Extra tests to check if the code deals correctly with memory areas too large to dump completely:
        uMax = cBugId.dxConfig["uMaxMemoryDumpSize"];
        aoTests.append(cTest(sISA,  ["DoubleFree",             uMax],                         "DoubleFree[4n] ed2.531"));
        aoTests.append(cTest(sISA,  ["DoubleFree",         uMax + 1],                         "DoubleFree[4n+1] ed2.531"));
        aoTests.append(cTest(sISA,  ["DoubleFree",         uMax + 4],                         "DoubleFree[4n] ed2.531"));
        
      # Misaligned free
      aoTests.append(cTest(sISA,    ["MisalignedFree",            1,  1],                     "MisalignedFree[1]+0 ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["MisalignedFree",            1,  2],                     "MisalignedFree[1]+1 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            2,  4],                     "MisalignedFree[2]+2 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            3,  6],                     "MisalignedFree[3]+3 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            4,  8],                     "MisalignedFree[4n]+4n ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            5,  10],                    "MisalignedFree[4n+1]+4n+1 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            2,  1],                     "MisalignedFree[2]@1 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            3,  2],                     "MisalignedFree[3]@2 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            4,  3],                     "MisalignedFree[4n]@3 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            5,  4],                     "MisalignedFree[4n+1]@4n ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            1,  -1],                    "MisalignedFree[1]-1 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            1,  -2],                    "MisalignedFree[1]-2 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            1,  -3],                    "MisalignedFree[1]-3 ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            1,  -4],                    "MisalignedFree[1]-4n ed2.531"));
        aoTests.append(cTest(sISA,  ["MisalignedFree",            1,  -5],                    "MisalignedFree[1]-4n-1 ed2.531"));
      # NULL pointers
      aoTests.append(cTest(sISA,    ["AccessViolation",   "Read",     1],                     "AVR@NULL+1 ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", 2],                         "AVR@NULL+2 ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", 3],                         "AVR@NULL+3 ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", 4],                         "AVR@NULL+4n ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", 5],                         "AVR@NULL+4n+1 ed2.531"));
      uSignPadding = {"x86": 0, "x64": 0xFFFFFFFF00000000}[sISA];
      aoTests.append(cTest(sISA,    ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFF],   "AVR@NULL-1 ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFE],   "AVR@NULL-2 ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFD],   "AVR@NULL-3 ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFC],   "AVR@NULL-4n ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFB],   "AVR@NULL-4n-1 ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFFA],   "AVR@NULL-4n-2 ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF9],   "AVR@NULL-4n-3 ed2.531"));
        aoTests.append(cTest(sISA,  ["AccessViolation",   "Read", uSignPadding+0xFFFFFFF8],   "AVR@NULL-4n ed2.531"));
      # These are detected by Page Heap / Application Verifier
      aoTests.append(cTest(sISA,    ["OutOfBounds", "Heap", "Write", 1, -1, 1],               "OOBW[1]-1~1#3416 ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["OutOfBounds", "Heap", "Write", 2, -2, 2],               "OOBW[2]-2~2#5eb1 ed2.531"));
        aoTests.append(cTest(sISA,  ["OutOfBounds", "Heap", "Write", 3, -3, 3],               "OOBW[3]-3~3#bcd7 ed2.531"));
        aoTests.append(cTest(sISA,  ["OutOfBounds", "Heap", "Write", 4, -4, 4],               "OOBW[4n]-4n~4n#6682 ed2.531"));
        aoTests.append(cTest(sISA,  ["OutOfBounds", "Heap", "Write", 5, -5, 5],              ("OOBW[4n+1]-4n-1~4n+1#5b96 ed2.531", # x64: First byte written overwrites endstamp padding
                                                                                              "OOBW[4n+1]-4n~4n#6682 ed2.531"))); # x86: First byte written overrwrites stack trace pointer and cannot be detected.
        aoTests.append(cTest(sISA,  ["OutOfBounds", "Heap", "Write", 1, -4, 5],               "OOBW[1]-4n~4n#6682 ed2.531")); # Last byte written is within bounds!
        aoTests.append(cTest(sISA,  ["OutOfBounds", "Heap", "Write", 1, -4, 5],               "OOBW[1]-4n~4n#6682 ed2.531")); # Last byte is within bounds!
      # Page heap does not appear to work for x86 tests on x64 platform.
      aoTests.append(cTest(sISA,    ["UseAfterFree", "Read",    1,  0],                       "UAFR[1]@0 ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   2,  1],                       "UAFW[2]@1 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Read",    3,  2],                       "UAFR[3]@2 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   4,  3],                       "UAFW[4n]@3 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Read",    5,  4],                       "UAFR[4n+1]@4n ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   6,  5],                       "UAFW[4n+2]@4n+1 ed2.531"));
      aoTests.append(cTest(sISA,    ["UseAfterFree", "Read",    1,  1],                       "OOBUAFR[1]+0 ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   2,  3],                       "OOBUAFW[2]+1 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Read",    3,  5],                       "OOBUAFR[3]+2 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   4,  7],                       "OOBUAFW[4n]+3 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Read",    5,  9],                       "OOBUAFR[4n+1]+4n ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   6, 11],                       "OOBUAFW[4n+2]+4n+1 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Read",    1, -1],                       "OOBUAFR[1]-1 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   1, -2],                       "OOBUAFW[1]-2 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Read",    1, -3],                       "OOBUAFR[1]-3 ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Write",   1, -4],                       "OOBUAFW[1]-4n ed2.531"));
        aoTests.append(cTest(sISA,  ["UseAfterFree", "Read",    1, -5],                       "OOBUAFR[1]-4n-1 ed2.531"));
      # These issues are not detected until they cause an access violation. Heap blocks may be aligned up to 0x10 bytes.
      aoTests.append(cTest(sISA,    ["BufferOverrun",   "Heap", "Read",   0xC, 5],            "OOBR[4n]+4n ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xD, 5],            "OOBR[4n+1]+3 ed2.531"));
        aoTests.append(cTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xE, 5],            "OOBR[4n+2]+2 ed2.531"));
        aoTests.append(cTest(sISA,  ["BufferOverrun",   "Heap", "Read",   0xF, 5],            "OOBR[4n+3]+1 ed2.531"));
      # These issues are detected when they cause an access violation, but earlier OOBWs took place that did not cause AVs.
      # This is detected and reported by application verifier because the page heap suffix was modified.
      aoTests.append(cTest(sISA,    ["BufferOverrun",   "Heap", "Write",  0xC, 5],            "OOBW[4n]+0~4n#6682 ed2.531"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xD, 5],            "OOBW[4n+1]+0~3#bcd7 ed2.531"));
        aoTests.append(cTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xE, 5],            "OOBW[4n+2]+0~2#5eb1 ed2.531"));
        aoTests.append(cTest(sISA,  ["BufferOverrun",   "Heap", "Write",  0xF, 5],            "OOBW[4n+3]+0~1#3416 ed2.531"));
        aoTests.append(cTest(sISA,  ["BufferOverrun",   "Heap", "Write", 0x10, 5],            "OOBW[4n]+0 ed2.531")); # First byte writen causes AV; no data hash
      # Stack based heap overflows can cause an access violation if the run off the end of the stack, or a debugbreak
      # when they overwrite the stack cookie and the function returns. Finding out how much to write to overwrite the
      # stack cookie but not run off the end of the stack requires a bit of dark magic. I've only tested these values
      # on x64!
      uSmash = sISA == "x64" and 0x200 or 0x100;
      aoTests.append(cTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, uSmash],       "OOBW@Stack ed2.531"));
      # The OS does not allocate a guard page at the top of the stack. Subsequently, there may be a writable allocation
      # there, and a large enough stack overflow will write way past the end of the stack before causing an AV. This
      # causes a different BugId, so this test is not reliable at the moment.
      # TODO: Reimplement BugId and add feature that adds guard pages to all virtual allocations.
      # aoTests.append(cTest(sISA,    ["BufferOverrun",  "Stack", "Write", 0x10, 0x100000],     "AVW[Stack]+0 ed2.531"));
      
      if bFullTestSuite:
        for (uBaseAddress, sDescription) in [
          # 0123456789ABCDEF
                 (0x44444444, "Unallocated"), # Not sure if this is guaranteed, but in my experience it's reliable.
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
            aoTests.append(cTest(sISA,  ["AccessViolation", "Read", uBaseAddress],              "AVR@%s ed2.531" % sDescription));
            if uBaseAddress >= 0x800000000000 and uBaseAddress < 0xffff800000000000:
              aoTests.append(cTest(sISA,  ["AccessViolation", "Write", uBaseAddress],           "AV_@%s ed2.531" % sDescription));
              aoTests.append(cTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],            "AVE@%s 46f.46f" % sDescription));
            else:
              aoTests.append(cTest(sISA,  ["AccessViolation", "Write", uBaseAddress],           "AVW@%s ed2.531" % sDescription));
              aoTests.append(cTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],            "AVE@%s 46f.ed2" % sDescription));
            aoTests.append(cTest(sISA,    ["AccessViolation", "Call", uBaseAddress],           ("AVE@%s f47.f47" % sDescription, "AVE@%s f47.ed2" % sDescription)));
      
      if bFullTestSuite:
        for (uBaseAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in ddtsDetails_uSpecialAddress_sISA[sISA].items():
          if uBaseAddress < (1 << 32) or (sISA == "x64" and uBaseAddress < (1 << 47)):
            aoTests.append(cTest(sISA,    ["AccessViolation", "Read", uBaseAddress],            "AVR@%s ed2.531" % sAddressId));
            if bFullTestSuite:
              aoTests.append(cTest(sISA,  ["AccessViolation", "Write", uBaseAddress],           "AVW@%s ed2.531" % sAddressId));
              aoTests.append(cTest(sISA,  ["AccessViolation", "Call", uBaseAddress],           ("AVE@%s f47.f47" % sAddressId, "AVE@%s f47.ed2" % sAddressId)));
              aoTests.append(cTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],           ("AVE@%s 46f.46f" % sAddressId, "AVE@%s 46f.ed2" % sAddressId)));
          elif sISA == "x64":
            aoTests.append(cTest(sISA,    ["AccessViolation", "Read", uBaseAddress],            "AVR@%s ed2.531" % sAddressId));
            if bFullTestSuite:
              aoTests.append(cTest(sISA,  ["AccessViolation", "Write", uBaseAddress],           "AV_@%s ed2.531" % sAddressId));
              aoTests.append(cTest(sISA,  ["AccessViolation", "Call", uBaseAddress],           ("AVE@%s f47.f47" % sAddressId, "AVE@%s f47.ed2" % sAddressId)));
              aoTests.append(cTest(sISA,  ["AccessViolation", "Jump", uBaseAddress],           ("AVE@%s 46f.46f" % sAddressId, "AVE@%s 46f.ed2" % sAddressId)));
  print "* Starting tests...";
  nStartTime = time.clock();

  def fErrorCallback():
    for oTest in aoTests:
      oTest.fStop();
  for oTest in aoTests:
    if bFailed:
      break;
    oTest.bGenerateReportHTML = bGenerateReportHTML;
    oTest.fRun(fErrorCallback);
  
  nTestTime = time.clock() - nStartTime;
  oOutputLock.acquire();
  print "* Testing completed in %s seconds" % (long(nTestTime * 1000) / 1000.0);
  if bFailed:
    print "- Tests failed."
    sys.exit(1);
  else:
    print "+ All tests passed!"
    sys.exit(0);
