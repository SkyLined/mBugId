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
dxBugIdConfig["uReserveRAM"] = 1024; # Simply test if reserving RAM works, not actually reserve any useful amount.
dxBugIdConfig["uArchitectureIndependentBugIdBits"] = 32; # Test architecture independent bug ids

asTestISAs = [sOSISA];
if sOSISA == "x64":
  asTestISAs.append("x86");

sReportsFolderName = FileSystem.fsPath(sBaseFolderPath, "Tests", "Reports");

dsBinaries_by_sISA = {
  "x86": os.path.join(sLocalFolderPath, r"bin\Tests_x86.exe"),
  "x64": os.path.join(sLocalFolderPath, r"bin\Tests_x64.exe"),
};

bFailed = False;
oOutputLock = threading.Lock();
# If you see weird exceptions, try lowering the number of parallel tests:
oConcurrentTestsSemaphore = threading.Semaphore(uSequentialTests);
class cTest(object):
  def __init__(oTest, sISA, asCommandLineArguments, sExpectedBugTypeId):
    oTest.sISA = sISA;
    oTest.asCommandLineArguments = asCommandLineArguments;
    oTest.sExpectedBugTypeId = sExpectedBugTypeId; # Can also be a tuple of valid values (e.g. PureCall/AppExit)
    oTest.bInternalException = False;
    oTest.bHasOutputLock = False;
    oTest.bGenerateReportHTML = True;
  
  def __str__(oTest):
    return "%s =%s=> %s" % (" ".join(oTest.asCommandLineArguments), oTest.sISA, repr(oTest.sExpectedBugTypeId));
  
  def fRun(oTest):
    global bFailed, oOutputLock;
    oConcurrentTestsSemaphore.acquire();
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
  
  def fFinishedHandler(oTest, oBugReport):
    global bFailed, oOutputLock;
    try:
      if not bFailed:
        oOutputLock and oOutputLock.acquire();
        oTest.bHasOutputLock = True;
        if oTest.sExpectedBugTypeId:
          if not oBugReport:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Expected:    %s" % repr(oTest.sExpectedBugTypeId);
            print "  Got nothing";
            bFailed = True;
          elif isinstance(oTest.sExpectedBugTypeId, tuple) and oBugReport.sBugTypeId in oTest.sExpectedBugTypeId:
            print "+ %s" % oTest;
          elif isinstance(oTest.sExpectedBugTypeId, str) and oBugReport.sBugTypeId == oTest.sExpectedBugTypeId:
            print "+ %s" % oTest;
          else:
            print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
            print "  Expected:    %s" % oTest.sExpectedBugTypeId;
            print "  Reported:    %s @ %s" % (oBugReport.sId, oBugReport.sBugLocation);
            print "               %s" % (oBugReport.sBugDescription);
            bFailed = True;
        elif oBugReport:
          print "- Failed test: %s" % " ".join([dsBinaries_by_sISA[oTest.sISA]] + oTest.asCommandLineArguments);
          print "  Expected no report";
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
  
  def fInternalExceptionHandler(oTest, oException):
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
    for sISA in asTestISAs:
      aoTests.append(cTest(sISA, ["Nop"], None)); # No exceptions, just a clean program exit.
      aoTests.append(cTest(sISA, ["CPUUsage"], "CPUUsage"));
      aoTests.append(cTest(sISA, ["AccessViolation", "Read", "1"], "AVR:NULL+1"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "2"], "AVR:NULL+2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "3"], "AVR:NULL+3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "4"], "AVR:NULL+4*N"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "5"], "AVR:NULL+4*N+1"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "6"], "AVR:NULL+4*N+2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "7"], "AVR:NULL+4*N+3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", "8"], "AVR:NULL+4*N"));
  #    if sISA != "x64": # Does not work on x64 dues to limitations of exception handling (See foAnalyzeException_STATUS_ACCESS_VIOLATION for details).
      sMinusPadding = {"x86": "", "x64": "FFFFFFFF"}[sISA];
      aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFFF"], "AVR:NULL-1"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFFE"], "AVR:NULL-2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFFD"], "AVR:NULL-3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFFC"], "AVR:NULL-4*N"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFFB"], "AVR:NULL-4*N-1"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFFA"], "AVR:NULL-4*N-2"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFF9"], "AVR:NULL-4*N-3"));
        aoTests.append(cTest(sISA, ["AccessViolation", "Read", sMinusPadding+"FFFFFFF8"], "AVR:NULL-4*N"));
      aoTests.append(cTest(sISA, ["Breakpoint"], "Breakpoint"));
      aoTests.append(cTest(sISA, ["C++"], ("C++", "C++:cException"))); # With and without symbols.
      aoTests.append(cTest(sISA, ["IntegerDivideByZero"], "IntegerDivideByZero"));
      aoTests.append(cTest(sISA, ["Numbered", "41414141", "42424242"], "0x41414141"));
      # Specific test to check for ntdll!RaiseException exception address being off-by-one from the stack address:
      aoTests.append(cTest(sISA, ["Numbered", "80000003", "1"], "Breakpoint"));
      aoTests.append(cTest(sISA, ["IllegalInstruction"], "IllegalInstruction"));
      aoTests.append(cTest(sISA, ["PrivilegedInstruction"], "PrivilegedInstruction"));
      aoTests.append(cTest(sISA, ["StackExhaustion"], "StackExhaustion"));
      aoTests.append(cTest(sISA, ["RecursiveCall"], "RecursiveCall"));
      aoTests.append(cTest(sISA, ["StaticBufferOverrun10", "Write", "20"], "OOBW[Stack]"));
#      aoTests.append(cTest(sISA, ["BufferOverrun", "Stack", "Write", "20", "100000"], "OOBW[Stack]"));
      # These are detected by Page Heap / Application Verifier
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "-1"], "OOBW[4*N]-1~1#b4b1"));  # Write the byte at offset -1 from the start of the buffer.
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "-4"], "OOBW[4*N]-4*N~1#b4b1"));  # Write the byte at offset -4 from the start of the buffer.
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c",  "c"], "OOBW[4*N]~1#b4b1"));    # Write the byte at offset 0 from the end of the buffer.
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c",  "d"], "OOBW[4*N]+1~1#b4b1"));  # Write the byte at offset 1 from the end of the buffer.
      # These are detected because they cause an access violation.
      aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "1c"], "OOBW[4*N]+4*N")); # Write the byte at offset 0x10 from the end of the buffer.
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "1d"], "OOBW[4*N]+4*N+1")); # Write the byte at offset 0x10 from the end of the buffer.
      # A pure virtual function call should result in an AppExit exception. However, sometimes the "binary!purecall" or
      # "binary!_purecall" function can be found on the stack to destinguish these specific cases. Wether this works
      # depends on the build of the application and whether symbols are being used.
      aoTests.append(cTest(sISA, ["PureCall"], ("AppExit", "PureCall")));
      # Page heap does not appear to work for x86 tests on x64 platform.
      aoTests.append(cTest(sISA, ["UseAfterFree", "Read", "20", "0"], "UAFR"));
      aoTests.append(cTest(sISA, ["UseAfterFree", "Write", "20", "0"], "UAFW"));
      # These issues are not detected until they cause an access violation; there is no way to detect and report OOBRs before this happens.
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", "20", "4"], "OOBR[4*N]"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", "1f", "4"], "OOBR[4*N+3]+1"));
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", "1e", "4"], "OOBR[4*N+2]+2"));
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Read", "1d", "4"], "OOBR[4*N+1]+3"));
      # These issues are detected when they cause an access violation, but earlier OOBWs took place that did not cause AVs.
      # This is detected and reported by application verifier because the page heap suffix was modified.
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", "20", "4"], "OOBW[4*N]"));
      aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", "1f", "4"], "OOBW[4*N+3]~1#b4b1"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", "1e", "4"], "OOBW[4*N+2]~2#4a7d"));
        aoTests.append(cTest(sISA, ["BufferOverrun", "Heap", "Write", "1d", "4"], "OOBW[4*N+1]~3#670b"));
#      aoTests.append(cTest(sISA, ["BufferUnderrun", "Heap", "Write", "20", "4"], "OOBR[4*N]-4~4#????"));
      if bFullTestSuite:
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "10"], "OOBR[4*N]+4*N"));    # Read byte at offset 4 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "11"], "OOBR[4*N]+4*N+1"));  # Read byte at offset 5 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "12"], "OOBR[4*N]+4*N+2"));  # Read byte at offset 6 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "13"], "OOBR[4*N]+4*N+3"));  # Read byte at offset 7 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Read", "c", "14"], "OOBR[4*N]+4*N"));    # Read byte at offset 8 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "10"], "OOBW[4*N]+4*N"));   # Write byte at offset 4 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "11"], "OOBW[4*N]+4*N+1")); # Write byte at offset 5 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "12"], "OOBW[4*N]+4*N+2")); # Write byte at offset 6 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "13"], "OOBW[4*N]+4*N+3")); # Write byte at offset 7 from the end of the memory block
        aoTests.append(cTest(sISA, ["OutOfBounds", "Heap", "Write", "c", "14"], "OOBW[4*N]+4*N"));   # Write byte at offset 8 from the end of the memory block
      if False:
        # This does not appear to work at all. TODO: fix this.
        aoTests.append(cTest(sISA, ["BufferOverrun", "Stack", "Write", "20", "1000"], "OOBW"));
      
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
              cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AVR:%s" % sDescription),
              cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AV_:%s" % sDescription),
            ]);
          else:
            aoTests.extend([
              cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AVR:%s" % sDescription),
              cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AVW:%s" % sDescription),
            ]);
          cTest(sISA, ["AccessViolation", "Call", "%X" % uBaseAddress], "AVE:%s" % sDescription),
          cTest(sISA, ["AccessViolation", "Jump", "%X" % uBaseAddress], "AVE:%s" % sDescription),
    
    for (sISA, dtsDetails_uSpecialAddress) in ddtsDetails_uSpecialAddress_sISA.items():
      for (uBaseAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
        if uBaseAddress < (1 << 32) or (sISA == "x64" and uBaseAddress < (1 << 47)):
          aoTests.append(cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AVR:%s" % sAddressId));
          aoTests.append(cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AVW:%s" % sAddressId));
          aoTests.append(cTest(sISA, ["AccessViolation", "Call", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
          aoTests.append(cTest(sISA, ["AccessViolation", "Jump", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
        elif sISA == "x64":
          aoTests.append(cTest(sISA, ["AccessViolation", "Read", "%X" % uBaseAddress], "AVR:%s" % sAddressId));
          aoTests.append(cTest(sISA, ["AccessViolation", "Write", "%X" % uBaseAddress], "AV_:%s" % sAddressId));
          aoTests.append(cTest(sISA, ["AccessViolation", "Call", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
          aoTests.append(cTest(sISA, ["AccessViolation", "Jump", "%X" % uBaseAddress], "AVE:%s" % sAddressId));
        if not bFullTestSuite:
          break;
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
