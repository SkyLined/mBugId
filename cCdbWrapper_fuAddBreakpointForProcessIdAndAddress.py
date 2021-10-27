import re;

grbSetBreakpointOutput = re.compile(
  rb"^\s*"
  rb"breakpoint "
  rb"(\d+)"
  rb" "
  rb"(?:"
    rb"exists, redefining"
  rb"|"
    rb"redefined"
  rb")"
  rb"\s*$"
);

def cCdbWrapper_fuAddBreakpointForProcessIdAndAddress(oCdbWrapper, uProcessId, uAddress, fCallback, u0ThreadId = None, sb0Command = None):
  # Find out if there is executable memory at the address requested, to determine if setting a breakpoint
  # there makes sense.
  oProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
  o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uAddress);
  if not o0VirtualAllocation or not o0VirtualAllocation.bExecutable:
    return None; # The memory at the given address is not allocated and/or executable.
  # Select the right process.
  oCdbWrapper.fSelectProcessId(uProcessId);
  # Put breakpoint only on relevant thread if provided.
  if u0ThreadId is not None:
    sb0Command = b".if (@$tid != 0x%X) {gh;}%s;" % (u0ThreadId, sb0Command is not None and b" .else {%s};" % sb0Command or b"");
  uBreakpointId = next(oCdbWrapper.oBreakpointCounter);
  sbBreakpointCommand = b".if ($vvalid(0x%X,1)) {bp%d 0x%X%s;}; .else {.echo Invalid address;};" % (
    uAddress, 
    uBreakpointId,
    uAddress, 
    (b' "%s"' % sb0Command.replace(b"\\", b"\\\\").replace(b'"', b'\\"')) if sb0Command else b""
  );
  asbBreakpointResult = oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = sbBreakpointCommand,
    sb0Comment = b"Set breakpoint",
  );
  # It could be that a previous breakpoint existed at the given location, in which case that breakpoint id is used
  # by cdb instead. This must be detected so we can return the correct breakpoint id to the caller and match the
  # callback to the right breakpoint as well.
  if (
    len(asbBreakpointResult) == 5
    and re.match(rb'^Unable to insert breakpoint %d at .*, Win32 error 0n\d+$' % uBreakpointId, asbBreakpointResult[0])
    and asbBreakpointResult[1] == b'    "Invalid access to memory location."'
    and asbBreakpointResult[2] == b'The breakpoint was set with BP.  If you want breakpoints'
    and asbBreakpointResult[3] == b'to track module load/unload state you must use BU.'
    and re.match(rb'^bp%d at .* failed$' % uBreakpointId, asbBreakpointResult[4])
  ):
    oCdbWrapper.fbFireCallbacks("Log message", "Cannot add breakpoint", {
      "Breakpoint id": "%d" % uBreakpointId,
      "Address": "0x%X" % uAddress,
      "Process id": "%d/0x%X" % (uProcessId, uProcessId),
      "Error": "Invalid access to memory location.",
    });
    return None;
  elif len(asbBreakpointResult) == 1:
    if asbBreakpointResult[0] == b"Invalid address":
      oCdbWrapper.fbFireCallbacks("Log message", "Cannot add breakpoint", {
        "Breakpoint id": "%d" % uBreakpointId,
        "Address": "0x%X" % uAddress,
        "Process id": "%d/0x%X" % (uProcessId, uProcessId),
        "Error": "Invalid address.",
      });
      return None;
    obActualBreakpointIdMatch = grbSetBreakpointOutput.match(asbBreakpointResult[0]);
    assert obActualBreakpointIdMatch, \
        "bad set breakpoint result:\r\n%s" % \
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbBreakpointResult);
    uBreakpointId = int(obActualBreakpointIdMatch.group(1));
    # This breakpoint must have been "removed" with fRemoveBreakpoint before a new breakpoint can be set at this
    # location. If it was not, throw an exception.
    assert uBreakpointId not in oCdbWrapper.dfCallback_by_uBreakpointId, \
        "Two active breakpoints at the same location is not supported";
  else:
    assert len(asbBreakpointResult) == 0, \
        "bad set breakpoint result\r\n%s" % \
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbBreakpointResult);
  oCdbWrapper.fbFireCallbacks("Log message", "Added breakpoint", {
    "Breakpoint id": "%d" % uBreakpointId,
    "Address": uAddress,
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
  });
  oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId] = uProcessId;
  oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId] = uAddress;
  oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId] = fCallback;
  if uAddress in oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId.get(uProcessId, []):
    oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId[uProcessId].remove(uAddress);
  return uBreakpointId;

