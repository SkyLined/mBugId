import re;

def cCdbWrapper_fuAddBreakpoint(oCdbWrapper, uAddress, fCallback, uProcessId, uThreadId = None, sCommand = None):
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
    oCdbWrapper.fLogMessageInReport(
      "LogBreakpoint",
      "Cannot add breakpoint %d at address 0x%X in process %d/0x%X." % (uBreakpointId, uAddress, uProcessId, uProcessId),
    );
    return None;
  elif len(asBreakpointResult) == 1:
    if asBreakpointResult[0] == "Invalid address":
      oCdbWrapper.fLogMessageInReport(
        "LogBreakpoint",
        "Cannot add breakpoint %d at address 0x%X in process %d/0x%X." % (uBreakpointId, uAddress, uProcessId, uProcessId),
      );
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
  oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId] = uAddress;
  oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId] = uProcessId;
  oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId] = fCallback;
  return uBreakpointId;

def cCdbWrapper_fRemoveBreakpoint(oCdbWrapper, uBreakpointId):
  uProcessId = oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
  oCdbWrapper.fSelectProcess(uProcessId);
  # There can be any number of breakpoints according to the docs, so no need to reuse them. There is a bug in cdb:
  # using "bc" to clear a breakpoint can still lead to a STATUS_BREAKPOINT exception at the original address later.
  # There is nothing to detect this exception was caused by this bug, and filtering these exceptions is therefore
  # hard to do correctly. An easier way to address this issue is to not "clear" the breakpoint, but replace the
  # command executed when the breakpoint is hit with "gh" (go with exception handled).
  asClearBreakpoint = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = 'bp%d "gh";' % uBreakpointId,
    sComment = 'Remove breakpoint',
  );
  del oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];