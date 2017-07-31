import signal, time;
from WindowsAPI import *;

def cCdbWrapper_fAskCdbToInterruptApplication(oCdbWrapper):
  assert oCdbWrapper.bApplicationIsRunnning, \
      "cdb cannot be asked to interrupt the application if the application is not running!";
  assert not oCdbWrapper.bCdbHasBeenAskedToInterruptApplication, \
      "cdb cannot be asked to interrupt the application twice!";
  assert KERNEL32.GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, oCdbWrapper.oCdbProcess.pid), \
      "Failed to send CTRL+BREAK to cdb process with id %d/0x%X" % (oCdbWrapper.oCdbProcess.pid, oCdbWrapper.oCdbProcess.pid);
  oCdbWrapper.bCdbHasBeenAskedToInterruptApplication = True;
