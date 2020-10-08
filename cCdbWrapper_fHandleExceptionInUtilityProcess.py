from mWindowsSDK import STATUS_ACCESS_VIOLATION, STATUS_STACK_BUFFER_OVERRUN;
from mWindowsAPI import fbTerminateForThreadId;

def cCdbWrapper_fHandleExceptionInUtilityProcess(oCdbWrapper, uExceptionCode, sRelatedErrorDefineName):
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
