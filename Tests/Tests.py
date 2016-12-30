import os, re, sys, threading;
sLocalFolderPath = os.path.dirname(os.path.abspath(__file__));
sBaseFolderPath = os.path.dirname(sLocalFolderPath);
sys.path.extend([os.path.join(sBaseFolderPath, x) for x in ["", "modules"]]);

bDebugStartFinish = False;  # Show some output when a test starts and finishes.
bDebugIO = False;           # Show cdb I/O during tests (you'll want to run only 1 test at a time for this).
uSequentialTests = 32;      # Run multiple tests simultaniously, values >32 will probably not work.
if bDebugIO: uSequentialTests = 1; # prevent UI mess

from cBugId import cBugId;
from cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION import ddtsDetails_uSpecialAddress_sISA;
from dxBugIdConfig import dxBugIdConfig;
from FileSystem import FileSystem;
from sOSISA import sOSISA;

dxBugIdConfig["bOutputStdIn"] = \
    dxBugIdConfig["bOutputStdOut"] = \
    dxBugIdConfig["bOutputStdErr"] = bDebugIO;
dxBugIdConfig["bOutputProcesses"] = False;
dxBugIdConfig["nExcessiveCPUUsageCheckInterval"] = 2; # The test application is simple: CPU usage should be apparent after a few seconds.
dxBugIdConfig["uReserveRAM"] = 1024; # Simply test if reserving RAM works, not actually reserve any useful amount.
dxBugIdConfig["uArchitectureIndependentBugIdBits"] = 32; # Test architecture independent bug ids

asTestISAs = [sOSISA];
if sOSISA == "x64":
  asTestISAs.append("x86");

sReportsFolderName = FileSystem.fsPath(sBaseFolderPath, "Tests", "Reports");

dsBinaries_by_sISA = {
  "x86": os.path.join(sLocalFolderPath, r"bin\Tests_x86.exe"),
  "x64": os.path.join(sLocalFolderPath, r"bin\Tests_x64.exe"),
  "fail": os.path.join(sLocalFolderPath, r"bin\Binary_does_not_exist.exe"),
};

bFailed = False;
oOutputLock = threading.Lock();
# If you see weird exceptions, try lowering the number of parallel tests:
oConcurrentTestsSemaphore = threading.Semaphore(uSequentialTests);
class cTest(object):
  def __init__(oTest, sISA, axCommandLineArguments, sExpectedBugTypeId, sExpectedFailedToDebugApplicationErrorMessage = None):
    oTest.sISA = sISA;
    oTest.asCommandLineArguments = [
      isinstance(x, str) and x
               or x < 10 and ("%d" % x)
                          or ("0x%X" % x)
      for x in axCommandLineArguments
    ];
    oTest.sExpectedBugTypeId = sExpectedBugTypeId; # Can also be a tuple of valid values (e.g. PureCall/AppExit)
    oTest.sExpectedFailedToDebugApplicationErrorMessage = sExpectedFailedToDebugApplicationErrorMessage;
    oTest.bHasOutputLock = False;
    oTest.bGenerateReportHTML = True;
  
  def __str__(oTest):
    return "%s =%s=> %s" % (" ".join(oTest.asCommandLineArguments), oTest.sISA, repr(oTest.sExpectedBugTypeId));
  
  def fRun(oTest):
    global bFailed, oOutputLock;
    oConcurrentTestsSemaphore.acquire();
    if oTest.sExpectedFailedToDebugApplicationErrorMessage:
      sBinary = "this:cannot:be:run";
    else:
      sBinary = dsBinaries_by_sISA[oTest.sISA];
    asApplicationCommandLine = [sBinary] + oTest.asCommandLineArguments;
    if bDebugStartFinish:
      oOutputLock and oOutputLock.acquire();
      oTest.bHasOutputLock = True;
      print "* Started %s" % oTest;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
    try:
      oTest.oBugId = cBugId(
        sCdbISA = oTest.sISA,
        asApplicationCommandLine = asApplicationCommandLine,
        asSymbolServerURLs = ["http://msdl.microsoft.com/download/symbols"], # Will be ignore if symbols are disabled.
        bGenerateReportHTML = oTest.bGenerateReportHTML,
        fFinishedCallback = oTest.fFinishedHandler,
        fInternalExceptionCallback = oTest.fInternalExceptionHandler,
      );
      oTest.oBugId.fStart();
      oTest.oBugId.fSetCheckForExcessiveCPUUsageTimeout(1);
    except Exception, oException:
      if not bFailed:
        bFailed = True;
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
        print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
        print "  Expected:    %s" % repr(oTest.sExpectedBugTypeId);
        print "  Exception:   %s" % repr(oException);
        oOutputLock and oOutputLock.release();
        oTest.bHasOutputLock = False;
        raise;
  
  def fWait(oTest):
    hasattr(oTest, "oBugId") and oTest.oBugId.fWait();
  
  def fFinished(oTest):
    if bDebugStartFinish:
      oOutputLock and oOutputLock.acquire();
      oTest.bHasOutputLock = True;
      print "* Finished %s" % oTest;
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
    oConcurrentTestsSemaphore.release();
  
  def fFinishedHandler(oTest, oBugId, oBugReport):
    global bFailed, oOutputLock;
    try:
      if not bFailed:
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
        if oTest.sExpectedFailedToDebugApplicationErrorMessage:
          if oBugId.sFailedToDebugApplicationErrorMessage != oTest.sExpectedFailedToDebugApplicationErrorMessage:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test should have reported a failure to debug the application.";
            print "  Expected:    %s" % repr(oTest.sExpectedFailedToDebugApplicationErrorMessage);
            print "  Reported:    %s" % repr(oBugId.sFailedToDebugApplicationErrorMessage);
            bFailed = True;
        elif oBugId.sFailedToDebugApplicationErrorMessage:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test was unabled to debug the application:";
            print "  Expected:    no error";
            print "  Reported:    %s" % repr(oBugId.sFailedToDebugApplicationErrorMessage);
        elif oTest.sExpectedBugTypeId:
          if not oBugReport:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test should have reported a bug in the application.";
            print "  Expected:    %s" % repr(oTest.sExpectedBugTypeId);
            print "  Reported:    no bug";
            bFailed = True;
          elif isinstance(oTest.sExpectedBugTypeId, tuple) and oBugReport.sBugTypeId in oTest.sExpectedBugTypeId:
            print "+ %s" % oTest;
          elif isinstance(oTest.sExpectedBugTypeId, str) and oBugReport.sBugTypeId == oTest.sExpectedBugTypeId:
            print "+ %s" % oTest;
          else:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Test reported a different bug than expected in the application.";
            print "  Expected:    %s" % oTest.sExpectedBugTypeId;
            print "  Reported:    %s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
            print "               %s" % (oBugReport.sBugDescription);
            bFailed = True;
        elif oBugReport:
          print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
          print "  Test reported an unexpected bug in the application.";
          print "  Expected:    no bug";
          print "  Reported:    %s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
          print "               %s" % (oBugReport.sBugDescription);
          bFailed = True;
        else:
          print "+ %s" % oTest;
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
  
  def fInternalExceptionHandler(oTest, oBugId, oException):
    global bFailed;
    oTest.fFinished();
    if not bFailed:
      # Exception in fFinishedHandler can cause this function to be executed with lock still in place.
      if not oTest.bHasOutputLock:
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
      bFailed = True;
      print "- Exception in %s: %s" % (oTest, oException);
      oOutputLock and oOutputLock.release();
      oTest.bHasOutputLock = False;
      raise;

if __name__ == "__main__":
  aoTests = [];
  bFullTestSuite = len(sys.argv) > 1 and sys.argv[1] == "--full";
  bGenerateReportHTML = bFullTestSuite;
  if not bFullTestSuite:
    # When we're not running the full test suite, we're not saving reports, so we don't need symbols.
    # Disabling symbols should speed things up considerably.
    dxBugIdConfig["asDefaultSymbolServerURLs"] = None;
  if len(sys.argv) > 1 and not bFullTestSuite:
    # Test is user supplied, output I/O
    dxBugIdConfig["bOutputStdIn"] = \
        dxBugIdConfig["bOutputStdOut"] = \
        dxBugIdConfig["bOutputStdErr"] = True;
    bGenerateReportHTML = True;
    aoTests.append(cTest(sys.argv[1], sys.argv[2:], None)); # Expect no exceptions.
  else:
    aoTests.append(cTest("x86", [], None, 'Failed to start application "this:cannot:be:run": Win32 error 0n2!\r\nDid you provide the correct the path and name of the executable?'));
    for sISA in asTestISAs:
      aoTests.append(cTest(sISA, ["Nop"], None)); # No exceptions, just a clean program exit.
      aoTests.append(cTest(sISA, ["CPUUsage"], "CPUUsage"));
      aoTests.append(cTest(sISA, ["MisalignedFree", 0x10, 8], "MisalignedFree[4*N]+4*N"));
      aoTests.append(cTest(sISA, ["AccessViolation", "Read", 1], "AVR:NULL+1"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", 2], "AVR:NULL+2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", 3], "AVR:NULL+3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", 4], "AVR:NULL+4*N"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", 5], "AVR:NULL+4*N+1"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", 6], "AVR:NULL+4*N+2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", 7], "AVR:NULL+4*N+3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", 8], "AVR:NULL+4*N"));
  #    if sISA != "x64": # Does not work on x64 dues to limitations of exception handling (See foAnalyzeException_STATUS_ACCESS_VIOLATION for details).
      uSignPadding = {"x86": 0, "x64": 0xFFFFFFFF00000000}[sISA];
      aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFFF], "AVR:NULL-1"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFFE], "AVR:NULL-2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFFD], "AVR:NULL-3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFFC], "AVR:NULL-4*N"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFFB], "AVR:NULL-4*N-1"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFFA], "AVR:NULL-4*N-2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFF9], "AVR:NULL-4*N-3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", uSignPadding+0xFFFFFFF8], "AVR:NULL-4*N"));
      aoTests.append(cTest(sISA, ["Breakpoint"], "Breakpoint"));
      aoTests.append(cTest(sISA, ["C++"], ("C++", "C++:cException"))); # With and without symbols.
      aoTests.append(cTest(sISA, ["IntegerDivideByZero"], "IntegerDivideByZero"));
      aoTests.append(cTest(sISA, ["Numbered", 0x41414141, 0x42424242], "0x41414141"));
      # Specific test to check for ntdll!RaiseException exception address being off-by-one from the stack address:
      aoTests.append(cTest(sISA, ["Numbered", 0x80000003, 1], "Breakpoint"));
      aoTests.append(cTest(sISA, ["IllegalInstruction"], "IllegalInstruction"));
      aoTests.append(cTest(sISA, ["PrivilegedInstruction"], "PrivilegedInstruction"));
      aoTests.append(cTest(sISA, ["StackExhaustion", 0x100], "StackExhaustion"));
      aoTests.append(cTest(sISA, ["RecursiveCall"], "RecursiveCall"));
### For some reason these do not work at the moment !?
#      # These are detected by Page Heap / Application Verifier
#      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, -1, 1], "OOBW[4*N]-1~1#3416"));  # Write the byte at offset -1 from the start of the buffer.
#      if bFullTestSuite:
#        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, -4, 1], "OOBW[4*N]-4*N~1#3416"));  # Write the byte at offset -4 from the start of the buffer.
#      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc,  0xc, 1], "OOBW[4*N]~1#3416"));    # Write the byte at offset 0 from the end of the buffer.
#      if bFullTestSuite:
#        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc,  0xd, 1], "OOBW[4*N]+1~1#3416"));  # Write the byte at offset 1 from the end of the buffer.
###
      # These are detected because they cause an access violation.
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, 0x1c, 1], "OOBW[4*N]+4*N")); # Write the byte at offset 0x10 from the end of the buffer.
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, 0x1d, 1], "OOBW[4*N]+4*N+1")); # Write the byte at offset 0x10 from the end of the buffer.
      # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
      # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
      # depends on the build of the application and whether symbols are being used.
      aoTests.append(cTest(sISA, ["PureCall"], ("AppExit", "PureCall")));
      # Page heap does not appear to work for x86 tests on x64 platform.
      aoTests.append(cTest(sISA, ["UseAfterFree", "Read", 0x20, 0], "UAFR[]~4*N"));
      aoTests.append(cTest(sISA, ["UseAfterFree", "Write", 0x20, 1], "UAFW[]~4*N+3"));
      aoTests.append(cTest(sISA, ["UseAfterFree", "Read", 0x20, 0x20], "OOBUAFR[]"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["UseAfterFree", "Write", 0x20, 0x31], "OOBUAFW[]+4*N+1"));
      # These issues are not detected until they cause an access violation; there is no way to detect and report OOBRs before this happens.
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", 0x20, 4], "OOBR[4*N]"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", 0x1f, 4], "OOBR[4*N+3]+1"));
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", 0x1e, 4], "OOBR[4*N+2]+2"));
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", 0x1d, 4], "OOBR[4*N+1]+3"));
      # These issues are detected when they cause an access violation, but earlier OOBWs took place that did not cause AVs.
      # This is detected and reported by application verifier because the page heap suffix was modified.
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", 0x20, 4], "OOBW[4*N]"));
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", 0x1f, 4], "OOBW[4*N+3]~1#3416"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", 0x1e, 4], "OOBW[4*N+2]~2#5eb1"));
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", 0x1d, 4], "OOBW[4*N+1]~3#bcd7"));
### For some reason these do not work at the moment !?
#      aoTests.append(cTest(sISA, ["BufferUnderrun", "Heap", "Write", 0x20, 4], "OOBR[4*N]-4~4#????"));
###
      ### Stack buffer overrun
### There is no guarantee that nothing is allocated immediately following the stack, and I've found that quite often
##  the contrary is true. this causes the OOBR to read beyond the end of the stack, then beyond the end of the next
##  page(s) and finally cause an AV much later. This leads to false reports...
#      aoTests.append(cTest(sISA, ["BufferOverrun", "Stack", "Read", 0x20, 0x100000], "OOBR[Stack]"));
###
### For some reason these do not work at the moment !?
#      aoTests.append(cTest(sISA, ["BufferOverrun", "Stack", "Write", 0x20, 0x100000], "OOBW[Stack]"));
###
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", 0xc, 0x10, 1], "OOBR[4*N]+4*N"));    # Read byte at offset 4 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", 0xc, 0x11, 1], "OOBR[4*N]+4*N+1"));  # Read byte at offset 5 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", 0xc, 0x12, 1], "OOBR[4*N]+4*N+2"));  # Read byte at offset 6 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", 0xc, 0x13, 1], "OOBR[4*N]+4*N+3"));  # Read byte at offset 7 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", 0xc, 0x14, 1], "OOBR[4*N]+4*N"));    # Read byte at offset 8 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, 0x10, 1], "OOBW[4*N]+4*N"));   # Write byte at offset 4 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, 0x11, 1], "OOBW[4*N]+4*N+1")); # Write byte at offset 5 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, 0x12, 1], "OOBW[4*N]+4*N+2")); # Write byte at offset 6 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, 0x13, 1], "OOBW[4*N]+4*N+3")); # Write byte at offset 7 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", 0xc, 0x14, 1], "OOBW[4*N]+4*N"));   # Write byte at offset 8 from the end of the memory block
      
      for (uBaseAddress, sDescription) in [
        # 0123456789ABCDEF
               (0x44444444, "Unallocated"), # Not sure if this is guaranteed, but in my experience it's reliable.
           (0x7ffffffdffff, "Unallocated"), # Highly unlikely to be allocated as it is at the very top of allocatable mem.
           (0x7ffffffe0000, "Reserved"),
           (0x7ffffffeffff, "Reserved"),
           (0x7fffffff0000, "Unallocated"),
           (0x7fffffffffff, "Unallocated"),
           (0x800000000000, "Invalid"),
       (0x8000000000000000, "Invalid"),
      ]:
        if uBaseAddress < (1 << 32) or sISA == "x64":
          # On x64, there are some limitations to exceptions occoring at addresses between the userland and kernelland
          # memory address ranges.
          if uBaseAddress >= 0x800000000000 and uBaseAddress < 0xffff800000000000:
            aoTests.extend([
              cTest(sISA, ["AccessViolation", "Read", uBaseAddress], "AVR:%s" % sDescription),
              cTest(sISA, ["AccessViolation", "Write", uBaseAddress], "AV_:%s" % sDescription),
            ]);
          else:
            aoTests.extend([
              cTest(sISA, ["AccessViolation", "Read", uBaseAddress], "AVR:%s" % sDescription),
              cTest(sISA, ["AccessViolation", "Write", uBaseAddress], "AVW:%s" % sDescription),
            ]);
          cTest(sISA, ["AccessViolation", "Call", uBaseAddress], "AVE:%s" % sDescription),
          cTest(sISA, ["AccessViolation", "Jump", uBaseAddress], "AVE:%s" % sDescription),
    
    for (sISA, dtsDetails_uSpecialAddress) in ddtsDetails_uSpecialAddress_sISA.items():
      for (uBaseAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
        if uBaseAddress < (1 << 32) or (sISA == "x64" and uBaseAddress < (1 << 47)):
          aoTests.append(cTest(sISA, ["AccessViolation", "Read", uBaseAddress], "AVR:%s" % sAddressId));
          if bFullTestSuite:
            aoTests.append(cTest(sISA, ["AccessViolation", "Write", uBaseAddress], "AVW:%s" % sAddressId));
            aoTests.append(cTest(sISA, ["AccessViolation", "Call", uBaseAddress], "AVE:%s" % sAddressId));
            aoTests.append(cTest(sISA, ["AccessViolation", "Jump", uBaseAddress], "AVE:%s" % sAddressId));
        elif sISA == "x64":
          aoTests.append(cTest(sISA, ["AccessViolation", "Read", uBaseAddress], "AVR:%s" % sAddressId));
          if bFullTestSuite:
            aoTests.append(cTest(sISA, ["AccessViolation", "Write", uBaseAddress], "AV_:%s" % sAddressId));
            aoTests.append(cTest(sISA, ["AccessViolation", "Call", uBaseAddress], "AVE:%s" % sAddressId));
            aoTests.append(cTest(sISA, ["AccessViolation", "Jump", uBaseAddress], "AVE:%s" % sAddressId));
  print "* Starting tests...";
  for oTest in aoTests:
    if bFailed:
      break;
    oTest.bGenerateReportHTML = bGenerateReportHTML;
    oTest.fRun();
  for oTest in aoTests:
    oTest.fWait();
  
  oOutputLock.acquire();
  if bFailed:
    print "- Tests failed."
    sys.exit(1);
  else:
    print "+ All tests passed!"
    sys.exit(0);
