from mWindowsSDK import STATUS_ACCESS_VIOLATION, STATUS_BREAKPOINT, STATUS_STACK_BUFFER_OVERRUN;
from mWindowsAPI import fbTerminateForThreadId;

def cCdbWrapper_fHandleExceptionInUtilityProcess(oCdbWrapper, uExceptionCode, sRelatedErrorDefineName):
  if uExceptionCode == STATUS_BREAKPOINT:
    # cdb.exe will start a new thread in the utility process and trigger a
    # breakpoint to halt execution when the user presses CTRL+C
    assert oCdbWrapper.oCdbCurrentWindowsAPIThread.uId != oCdbWrapper.uUtilityInterruptThreadId, \
        "Unexpected exception 0x%08X (%s) in utility process." % (uExceptionCode, sRelatedErrorDefineName,);
    # The user pressed CTRL+BREAK: stop debugging
    oCdbWrapper.fbFireCallbacks("Log message", "User interrupted BugId using CTRL+BREAK.");
    oCdbWrapper.fStop();
  else:
    # We started a new thread in the utility process and trigger an access violation
    # to halt execution.
    assert oCdbWrapper.oCdbCurrentWindowsAPIThread.uId == oCdbWrapper.uUtilityInterruptThreadId, \
        "Unexpected exception 0x%08X (%s) in utility process thread 0x%X." % (uExceptionCode, sRelatedErrorDefineName, oCdbWrapper.oCdbCurrentWindowsAPIThread.uId);
    assert uExceptionCode in [STATUS_ACCESS_VIOLATION, STATUS_STACK_BUFFER_OVERRUN], \
        "Unexpected exception 0x%08X (%s) in utility process interrupt thread 0x%X." % (uExceptionCode, sRelatedErrorDefineName, oCdbWrapper.oCdbCurrentWindowsAPIThread.uId);
    # Terminate the thread in which we triggered an AV, so the utility process can continue running.
    # Since it is suspended, it will not terminate when we ask it to.
    assert not fbTerminateForThreadId(oCdbWrapper.uUtilityInterruptThreadId, bWait = False), \
        "Expected thread to still be suspended, but it was terminated";
    # Mark the interrupt as handled.
    oCdbWrapper.uUtilityInterruptThreadId = None;
    oCdbWrapper.fbFireCallbacks("Log message", "Application interrupted");
