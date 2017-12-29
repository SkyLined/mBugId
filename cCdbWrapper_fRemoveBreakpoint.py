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
  oCdbWrapper.fbFireEvent("Log message", "Removed breakpoint", {
    "Breakpoint id": "%d" % uBreakpointId,
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
  });
  del oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
  del oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
