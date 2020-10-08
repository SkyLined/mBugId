def cCdbWrapper_fRemoveBreakpoint(oCdbWrapper, uBreakpointId):
  uProcessId = oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
  oCdbWrapper.fSelectProcessId(uProcessId);
  # There can be any number of breakpoints according to the docs, so no need to reuse them. There is a bug in cdb:
  # using "bc" to clear a breakpoint can still lead to a STATUS_BREAKPOINT exception at the original address later.
# The following is not true:
#  # There is nothing to detect this exception was caused by this bug, and filtering these exceptions is therefore
#  # hard to do correctly. An easier way to address this issue is to not "clear" the breakpoint, but replace the
#  # command executed when the breakpoint is hit with "gh" (go with exception handled).
#  asClearBreakpoint = oCdbWrapper.fasExecuteCdbCommand(
#    sCommand = 'bp%d "gh";' % uBreakpointId,
#    sComment = 'Remove breakpoint',
#  );
  # Actually, we can add the address to a list of old breakpoints and ignore any STATUS_BREAKPOINT exception at this
  # address. There is a chance that the original instruction at this address triggers a STATUS_BREAKPOINT exception,
  # but I expect that chance to be negligable.
  asClearBreakpoint = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = 'bc%d;' % uBreakpointId,
    sComment = 'Remove breakpoint',
  );
  oCdbWrapper.fbFireCallbacks("Log message", "Removed breakpoint", {
    "Breakpoint id": "%d" % uBreakpointId,
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
  });
  uAddress = oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId];
  oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId.setdefault(uProcessId, []).append(uAddress);
  del oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
  del oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId];
  del oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
