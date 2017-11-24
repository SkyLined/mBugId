def cCdbWrapper_fbAttachToProcessForId(oCdbWrapper, uProcessId):
  asAttachToProcessOutput = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".attach -b 0x%X;" % uProcessId,
    sComment = "Attach to process %d" % uProcessId,
  );
  if asAttachToProcessOutput == [
    "Cannot debug pid %d, Win32 error 0x87" % uProcessId,
    '    "The parameter is incorrect."',
    "Unable to initialize target, Win32 error 0n87"
  ]:
    return False;
  assert asAttachToProcessOutput == ["Attach will occur on next execution"], \
      "Unexpected .attach output: %s" % repr(asAttachToProcessOutput);
  return True;
