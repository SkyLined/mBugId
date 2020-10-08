import signal, time;

from mWindowsAPI import fuCreateThreadForProcessIdAndAddress;

def cCdbWrapper_fInterruptApplicationExecution(oCdbWrapper):
  if oCdbWrapper.uUtilityInterruptThreadId is not None:
#    print "Interrupt ignored: already interrupting...";
    return; # We already interrupted the application; there is no need to do this again.
  # Asking cdb to interrupt the application can cause it to inject a thread that triggers an int 3. Unfortunately,
  # we have no reliable way of determining if this is the case or if the application itself has triggered an int 3.
  #
  # To remove any confusion, we will create a utility process that we also debug. In this utility process, we will
  # create a new thread and have it attempt to execute code at address 0. This will cause an access violation, which
  # will interrupt the application and cause cdb to report it. We can easily distinguish this exception from any other
  # exception caused by the target application because it will be reported to have happened in the utility process.
  if not oCdbWrapper.bCdbRunning:
#    print "Interrupt ignored: cdb not running...";
    return;
  if not oCdbWrapper.bApplicationIsRunning:
#    print "Interrupt ignored: application not running...";
    return;
  oCdbWrapper.uUtilityInterruptThreadId = fuCreateThreadForProcessIdAndAddress(oCdbWrapper.oUtilityProcess.uId, 0x0);
