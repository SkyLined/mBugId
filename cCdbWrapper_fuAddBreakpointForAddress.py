import re;

def cCdbWrapper_fuAddBreakpointForAddress(oCdbWrapper, uAddress, fCallback, uProcessId, uThreadId = None, sCommand = None):
  # Select the right process.
  oCdbWrapper.fSelectProcess(uProcessId);
  # Put breakpoint only on relevant thread if provided.
  if uThreadId is not None:
    sCommand = ".if (@$tid != 0x%X) {gh;}%s;" % (uThreadId, sCommand is not None and " .else {%s};" % sCommand or "");
  uBreakpointId = oCdbWrapper.oBreakpointCounter.next();
  sBreakpointCommand = ".if ($vvalid(0x%X,1)) {bp%d 0x%X%s;}; .else {.echo Invalid address;};" % (
    uAddress, 
    uBreakpointId,
    uAddress, 
    sCommand and (' "%s"' % sCommand.replace("\\", "\\\\").replace('"', '\\"')) or ""
  );
  asBreakpointResult = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = sBreakpointCommand,
    sComment = "Set breakpoint",
  );
  # It could be that a previous breakpoint existed at the given location, in which case that breakpoint id is used
  # by cdb instead. This must be detected so we can return the correct breakpoint id to the caller and match the
  # callback to the right breakpoint as well.
  if (
    len(asBreakpointResult) == 5
    and re.match(r'^Unable to insert breakpoint %d at .*, Win32 error 0n\d+$' % uBreakpointId, asBreakpointResult[0])
    and asBreakpointResult[1] == '    "Invalid access to memory location."'
    and asBreakpointResult[2] == 'The breakpoint was set with BP.  If you want breakpoints'
    and asBreakpointResult[3] == 'to track module load/unload state you must use BU.'
    and re.match(r'^bp%d at .* failed$' % uBreakpointId, asBreakpointResult[4])
  ):
    oCdbWrapper.fbFireEvent("Log message", "Cannot add breakpoint", {
      "Breakpoint id": "%d" % uBreakpointId,
      "Address": "0x%X" % uAddress,
      "Process id": "%d/0x%X" % (uProcessId, uProcessId),
      "Error": "Invalid access to memory location.",
    });
    return None;
  elif len(asBreakpointResult) == 1:
    if asBreakpointResult[0] == "Invalid address":
      oCdbWrapper.fbFireEvent("Log message", "Cannot add breakpoint", {
        "Breakpoint id": "%d" % uBreakpointId,
        "Address": "0x%X" % uAddress,
        "Process id": "%d/0x%X" % (uProcessId, uProcessId),
        "Error": "Invalid address.",
      });
      return None;
    oActualBreakpointIdMatch = re.match(r"^breakpoint (\d+) (?:exists, redefining|redefined)$", asBreakpointResult[0]);
    assert oActualBreakpointIdMatch, \
        "bad breakpoint result\r\n%s" % "\r\n".join(asBreakpointResult);
    uBreakpointId = long(oActualBreakpointIdMatch.group(1));
    # This breakpoint must have been "removed" with fRemoveBreakpoint before a new breakpoint can be set at this
    # location. If it was not, throw an exception.
    assert uBreakpointId not in oCdbWrapper.dfCallback_by_uBreakpointId, \
        "Two active breakpoints at the same location is not supported";
  else:
    assert len(asBreakpointResult) == 0, \
        "bad breakpoint result\r\n%s" % "\r\n".join(asBreakpointResult);
  oCdbWrapper.fbFireEvent("Log message", "Added breakpoint", {
    "Breakpoint id": "%d" % uBreakpointId,
    "Address": uAddress,
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
  });
  oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId] = uProcessId;
  oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId] = fCallback;
  return uBreakpointId;

