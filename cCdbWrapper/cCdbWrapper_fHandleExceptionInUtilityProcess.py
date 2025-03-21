from mWindowsSDK import STATUS_ACCESS_VIOLATION, STATUS_BREAKPOINT, STATUS_STACK_BUFFER_OVERRUN;
from mWindowsAPI import fbTerminateForThreadId;

def cCdbWrapper_fHandleExceptionInUtilityProcess(oCdbWrapper, uExceptionCode, sRelatedErrorDefineName):
  if oCdbWrapper.oCdbCurrentWindowsAPIThread.uId != oCdbWrapper.uUtilityInterruptThreadId:
    oCdbWrapper.fbFireCallbacks(
      "Log message",
      "Ignored unexpected exception in utility process thread %d: 0x%X %s." % (
          oCdbWrapper.oCdbCurrentWindowsAPIThread.uId,
          uExceptionCode,
          sRelatedErrorDefineName,
      ));
  elif uExceptionCode == STATUS_BREAKPOINT:
    # cdb.exe will start a new thread in the utility process and trigger a
    # breakpoint to halt execution when the user presses CTRL+C
    # The user pressed CTRL+BREAK: stop debugging
    oCdbWrapper.fbFireCallbacks(
      "Log message",
      "Ignored unexpected STATUS_BREAKPOINT exception in utility process interrupt thread %d." % (
          oCdbWrapper.oCdbCurrentWindowsAPIThread.uId,
      ));
    return
    oCdbWrapper.fbFireCallbacks(
      "Log message",
      "User interrupted BugId using CTRL+BREAK.",
    );
    oCdbWrapper.fStop();
  elif uExceptionCode in [STATUS_ACCESS_VIOLATION, STATUS_STACK_BUFFER_OVERRUN]:
    # We started a new thread in the utility process and triggered an access violation
    # to halt execution.
    # Terminate the thread in which we triggered an AV, so the utility process can continue running.
    # Since it is suspended, it will not terminate immediately, so we don't wait for it.
    assert not fbTerminateForThreadId(oCdbWrapper.uUtilityInterruptThreadId, bWait = False), \
        "Expected thread to still be suspended, but it was terminated";
    # Mark the interrupt as handled.
    oCdbWrapper.uUtilityInterruptThreadId = None;
    oCdbWrapper.fbFireCallbacks(
      "Log message",
      "Application interrupted",
    );
  else:
    oCdbWrapper.fbFireCallbacks(
      "Log message",
      "Ignored unexpected exception in utility process utility thread %d: 0x%X %s." % (
          oCdbWrapper.oCdbCurrentWindowsAPIThread.uId,
          uExceptionCode,
          sRelatedErrorDefineName,
      ));
