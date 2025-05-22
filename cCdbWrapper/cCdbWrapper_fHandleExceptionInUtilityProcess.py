from mWindowsAPI import fbTerminateForThreadId;
from mWindowsSDK import STATUS_ACCESS_VIOLATION, STATUS_BREAKPOINT, STATUS_STACK_BUFFER_OVERRUN;

def cCdbWrapper_fHandleExceptionInUtilityProcess(oCdbWrapper, uExceptionCode, sRelatedErrorDefineName):
  if uExceptionCode == STATUS_BREAKPOINT:
    if oCdbWrapper.oCdbCurrentWindowsAPIThread.uId != oCdbWrapper.u0UtilityInterruptThreadId:
      # cdb.exe will start a new thread in the utility process and trigger a
      # breakpoint to halt execution when the user presses CTRL+C
      # The user pressed CTRL+BREAK: stop debugging
      oCdbWrapper.fbFireCallbacks(
        "Log message",
        "User interrupted BugId using CTRL+BREAK.",
      );
      oCdbWrapper.fStop();
    # debug breakpoints in the interrupt thread in the utility process are unwanted
    # but cannot be avoided, so we ignore them.
  elif uExceptionCode in [STATUS_ACCESS_VIOLATION, STATUS_STACK_BUFFER_OVERRUN]:
    if oCdbWrapper.oCdbCurrentWindowsAPIThread.uId == oCdbWrapper.u0PreviousUtilityInterruptThreadId:
      oCdbWrapper.fbFireCallbacks("Log message", "Interrupt thread access violation echo ignored in utility process", {
        "Thread id": oCdbWrapper.u0UtilityInterruptThreadId,
      });
      return;
    oCdbWrapper.fbFireCallbacks("Log message", "Interrupt thread access violation handled in utility process", {
      "Thread id": oCdbWrapper.u0UtilityInterruptThreadId,
    });
    # cdb has two bugs:
    # * on x86, it will freak out if we terminate the thread now, so we will
    #   need to suspend the thread to prevent the unhandled exception from
    #   terminating the utility process, and terminate it later. We terminate
    #   it once we want to interrupt the application again.
    # * on x64, it will report the access violation in the utility process over
    #   and over if we suspend the process, so we terminate the thread now.
    if oCdbWrapper.sCdbISA == "x86":
      oCdbWrapper.fasbExecuteCdbCommand(
        sbCommand = b"~;~f;~",
        sb0Comment = b"Suspend thread to prevent AV from terminating the process",
      );
      oCdbWrapper.fbFireCallbacks("Log message", "Interrupt thread suspended in utility process", {
        "Thread id": oCdbWrapper.u0UtilityInterruptThreadId,
      });
      oCdbWrapper.u0PreviousUtilityInterruptThreadId = oCdbWrapper.u0UtilityInterruptThreadId;
    else:
      oCdbWrapper.fbFireCallbacks("Log message", "Interrupt thread terminated in utility process", {
        "Thread id": oCdbWrapper.u0UtilityInterruptThreadId,
      });
      assert not fbTerminateForThreadId(oCdbWrapper.u0UtilityInterruptThreadId, bWait = False), \
          "Could not terminate previous utility process interrupt thread";
    oCdbWrapper.u0UtilityInterruptThreadId = None;
    # We started a new thread in the utility process and triggered an access violation
    # to halt execution.
    # Terminate the thread in which we triggered an AV, so the utility process can continue running.
    # Since it is suspended, it will not terminate immediately, so we don't wait for it.
    # Mark the interrupt as handled.
    oCdbWrapper.fbFireCallbacks(
      "Log message",
      "Application interrupted",
    );
  else:
    raise AssertionError(
      "Unhandled exception in utility process utility thread %d: 0x%X %s." % (
          oCdbWrapper.u0UtilityInterruptThreadId,
          uExceptionCode,
          sRelatedErrorDefineName,
      ));
