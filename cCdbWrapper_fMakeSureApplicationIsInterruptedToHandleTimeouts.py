import signal, time;
from WindowsAPI import *;

def cCdbWrapper_fMakeSureApplicationIsInterruptedToHandleTimeouts(oCdbWrapper):
  # Let the StdIO thread know a break exception was sent so it knows to expected cdb to report one (otherwise
  # it would get reported as a bug!).
  oCdbWrapper.uCdbBreakExceptionsPending += 1;
  assert KERNEL32.GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, oCdbWrapper.oCdbProcess.pid), \
      "Failed to send CTRL+BREAK to cdb process with id %d/0x%X" % (oCdbWrapper.oCdbProcess.pid, oCdbWrapper.oCdbProcess.pid);
