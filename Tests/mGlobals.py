import os;
sTestsFolderPath = os.path.dirname(os.path.abspath(__file__));
from mWindowsAPI import oSystemInfo;

# Variables used to store global settings for tests.
# Some of these can be provided through command line arguments.
gbDebugStartFinish = False;  # Show some output when a test starts and finishes.
gbShowCdbIO = False;          # Show cdb I/O during tests (you'll want to run only 1 test at a time for this).
gbShowApplicationIO = False;
gbLicenseWarningsShown = False;
gnExcessiveCPUUsageCheckInitialTimeoutInSeconds = 0.5; # CPU usage should normalize after half a second.
gbGenerateReportHTML = False;
gbSaveReportHTML = False;
guTotalMaxMemoryUse =  0x01234567; # The test application memory use limit: it should be large enough to allow the test
                                   # to function, but small enough to detect excessive memory use before the entire
                                   # system runs low on memory.
guOOMAllocationBlockSize = 0x1234; # The out-of-memory test allocations size. it should be large enough to cause OOM
                                   # reasonably fast, but small enough so a not to hit the guTotalMaxMemoryUse
                                   # immediately, as this would not represent a normal OOM scenario.
guLargeHeapBlockSize = 0x00800000; # Should be large to detect potential issues when handling large allocations, but
                                   # not so large as to cause the application to allocate more memory than it is allowed
                                   # through the guTotalMaxMemoryUse variable.

gdsTestsBinaries_by_sISA = {
  "x86": os.path.join(sTestsFolderPath, "bin", "Tests_x86.exe"),
  "x64": os.path.join(sTestsFolderPath, "bin", "Tests_x64.exe"),
};

gdsComSpec_by_sISA = {
  oSystemInfo.sOSISA: os.path.join(os.environ.get("WinDir"), "System32", "cmd.exe"),
};
if oSystemInfo.sOSISA == "x64":
  gdsComSpec_by_sISA["x86"] = os.path.join(os.environ.get("WinDir"), "SysWOW64", "cmd.exe");
