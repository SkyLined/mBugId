def cCdbWrapper_fAttachCdbToProcessForId(oCdbWrapper, uProcessId):
  oCdbWrapper.fbFireCallbacks("Log message", "Attaching to process", {
    "Process": "%d/0x%X" % (uProcessId, uProcessId),
  });
  asbAttachToProcessOutput = oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b".attach 0x%X;" % uProcessId,
    sb0Comment = b"Attach to process %d" % uProcessId,
  );
  if asbAttachToProcessOutput == [
    b"Cannot debug pid %d, Win32 error 0n87" % uProcessId,
    b'    "The parameter is incorrect."',
    b"Unable to initialize target, Win32 error 0n87",
  ]:
    sMessage = "Unable to attach to new process %d/0x%X" % (uProcessId, uProcessId);
    assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
        sMessage;
    oCdbWrapper.fStop();
  elif asbAttachToProcessOutput == [
    b"Cannot debug pid %d, NTSTATUS 0xC000010A"% uProcessId,
    b'    "An attempt was made to access an exiting process."',
    b'Unable to initialize target, NTSTATUS 0xC000010A',
  ]:
    sMessage = "Unable to attach to process %d/0x%X because it is terminating." % (uProcessId, uProcessId);
    assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sMessage), \
        sMessage;
    oCdbWrapper.fStop();
  else:
    assert asbAttachToProcessOutput == [
      b"Attach will occur on next execution"
    ], \
        "Unexpected .attach output: %s" % repr(asbAttachToProcessOutput);
