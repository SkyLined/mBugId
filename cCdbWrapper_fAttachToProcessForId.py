def cCdbWrapper_fAttachToProcessForId(oCdbWrapper, uProcessId, bMustBeResumed = False):
  assert oCdbWrapper.oCdbConsoleProcess is not None, \
      "You cannot attach to a process when cdb is not running."
  # Note that we're attaching to this process
  oCdbWrapper.auProcessIdsPendingAttach.append(uProcessId);
  if bMustBeResumed:
    oCdbWrapper.auProcessIdsThatNeedToBeResumedAfterAttaching.append(uProcessId);
  def fAttachToProcessHelper():
    # Report 
    oCdbWrapper.fbFireEvent("Log message", "Attaching to process", {
      "Process": "%d/0x%X" % (uProcessId, uProcessId),
    });
    asAttachToProcessOutput = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = ".attach 0x%X;" % uProcessId,
      sComment = "Attach to process %d" % uProcessId,
    );
    if asAttachToProcessOutput == [
      "Cannot debug pid %d, Win32 error 0x87" % uProcessId,
      '    "The parameter is incorrect."',
      "Unable to initialize target, Win32 error 0n87"
    ]:
      sMessage = "Unable to attach to new process %d/0x%X" % (oConsoleProcess.uId, oConsoleProcess.uId);
      assert oCdbWrapper.fbFireEvent("Failed to debug application", sMessage), \
          sMessage;
      oCdbWrapper.fStop();
    else:
      assert asAttachToProcessOutput == ["Attach will occur on next execution"], \
          "Unexpected .attach output: %s" % repr(asAttachToProcessOutput);
  oCdbWrapper.fInterrupt(
    "Attaching to process %d/0x%X" % (uProcessId, uProcessId),
    fAttachToProcessHelper,
  );
