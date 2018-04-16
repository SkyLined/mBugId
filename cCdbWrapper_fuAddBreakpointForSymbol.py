import re;

def cCdbWrapper_fuAddBreakpointForSymbol(oCdbWrapper, sSymbol, fCallback, uProcessId, uThreadId = None, sCommand = None):
  # Select the right process.
  oCdbWrapper.fSelectProcess(uProcessId);
  # Put breakpoint only on relevant thread if provided.
  if uThreadId is not None:
    sCommand = ".if (@$tid != 0x%X) {gh;}%s;" % (uThreadId, sCommand is not None and " .else {%s};" % sCommand or "");
  uBreakpointId = oCdbWrapper.oBreakpointCounter.next();
  sBreakpointCommand = "bu%d %s%s;" % (
    uBreakpointId,
    sSymbol, 
    sCommand and (' "%s"' % sCommand.replace("\\", "\\\\").replace('"', '\\"')) or ""
  );
  asBreakpointResult = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = sBreakpointCommand,
    sComment = "Set breakpoint",
  );
  # It could be that a previous breakpoint existed at the given location, in which case that breakpoint id is used
  # by cdb instead. This must be detected so we can return the correct breakpoint id to the caller and match the
  # callback to the right breakpoint as well.
  if len(asBreakpointResult) == 1:
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
    "Symbol": sSymbol,
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
  });
  oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId] = uProcessId;
  oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId] = fCallback;
  return uBreakpointId;

