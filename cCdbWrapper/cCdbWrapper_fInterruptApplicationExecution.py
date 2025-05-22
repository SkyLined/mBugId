from mWindowsAPI import fbTerminateForThreadId, fuCreateThreadForProcessIdAndAddress;
from mMultiThreading import cLock;

# We want to avoid multiple threads executing this code in parallel, as that
# could cause TOCTOU issues. We will use a lock to ensure that is can only be
# executed serially. The lock should only ever be held for a few milliseconds,
# so report a deadlock if it takes longer than 10 seconds to acquire the lock.
# There is no scenario in which this is expected to happen though.
oLock = cLock(n0DeadlockTimeoutInSeconds = 10);

def cCdbWrapper_fInterruptApplicationExecution(oCdbWrapper):
  oLock.fAcquire();
  try:
    assert oCdbWrapper.u0UtilityInterruptThreadId is None, \
        "Interrupt thread 0x%X already created!" % oCdbWrapper.u0UtilityInterruptThreadId;
    if oCdbWrapper.u0PreviousUtilityInterruptThreadId:
      oCdbWrapper.fbFireCallbacks("Log message", "Previous interrupt thread terminated in utility process", {
        "Thread id": oCdbWrapper.u0PreviousUtilityInterruptThreadId,
      });
      assert not fbTerminateForThreadId(oCdbWrapper.u0PreviousUtilityInterruptThreadId, bWait = False), \
          "Could not terminate previous utility process interrupt thread";
      oCdbWrapper.u0PreviousUtilityInterruptThreadId = None;
    # Asking cdb to interrupt the application can cause it to inject a thread that triggers an int 3. Unfortunately,
    # we have no reliable way of determining if this is the case or if the application itself has triggered an int 3.
    #
    # To remove any confusion, we will create a utility process that we also debug. In this utility process, we will
    # create a new thread and have it attempt to execute code at address 0. This will cause an access violation, which
    # will interrupt the application and cause cdb to report it. We can easily distinguish this exception from any other
    # exception caused by the target application because it will be reported to have happened in the utility process.
    assert oCdbWrapper.bCdbIsRunning, \
        "Cannot interrupt application if cdb is not running!";
    assert oCdbWrapper.bApplicationIsRunning, \
        "Cannot interrupt application if it is not running!";
    oCdbWrapper.u0UtilityInterruptThreadId = fuCreateThreadForProcessIdAndAddress(oCdbWrapper.oUtilityProcess.uId, 0xB1D); # B1D -> BugId
    oCdbWrapper.fbFireCallbacks("Log message", "Interrupt thread created in utility process", {
      "Thread id": oCdbWrapper.u0UtilityInterruptThreadId,
    });
    print("#" * 80);
    print("### INTERRUPT THREAD ID: 0x%X (access violation queued)" % oCdbWrapper.u0UtilityInterruptThreadId);
    print("#" * 80);
  finally:
    oLock.fRelease();