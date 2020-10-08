def cCdbWrapper_fAttachCdbToProcessForId(oCdbWrapper, uProcessId):
  oCdbWrapper.fbFireCallbacks("Log message", "Attaching to process", {
    "Process": "%d/0x%X" % (uProcessId, uProcessId),
  });
  asAttachToProcessOutput = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".attach 0x%X;" % uProcessId,
    sComment = "Attach to process %d" % uProcessId,
  );
  if asAttachToProcessOutput == [
    "Cannot debug pid %d, Win32 error 0n87" % uProcessId,
    '    "The parameter is incorrect."',
    "Unable to initialize target, Win32 error 0n87",
  ]:
    sMessage = "Unable to attach to new process %d/0x%X" % (uProcessId, uProcessId);
    assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
        sMessage;
    oCdbWrapper.fStop();
  elif asAttachToProcessOutput == [
    "Cannot debug pid %d, NTSTATUS 0xC000010A"% uProcessId,
    '    "An attempt was made to access an exiting process."',
    'Unable to initialize target, NTSTATUS 0xC000010A',
  ]:
    sMessage = "Unable to attach to process %d/0x%X because it is terminating." % (uProcessId, uProcessId);
    assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
        sMessage;
    oCdbWrapper.fStop();
  else:
    assert asAttachToProcessOutput == ["Attach will occur on next execution"], \
        "Unexpected .attach output: %s" % repr(asAttachToProcessOutput);
