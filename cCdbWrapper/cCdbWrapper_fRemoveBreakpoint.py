def cCdbWrapper_fRemoveBreakpoint(oCdbWrapper, uBreakpointId):
  uProcessId = oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
  oCdbWrapper.fSelectProcessId(uProcessId);
  # There is a bug in cdb where using "bc" to clear a breakpoint can still lead to a STATUS_BREAKPOINT exception at
  # the original address later. To work around this, we add the address of the breakpoint to a list of old breakpoints
  # and ignore any STATUS_BREAKPOINT exception at this address. There is a chance that the original instruction at
  # the breakpoint address triggers a real STATUS_BREAKPOINT exception, which we would then ignore by mistake.
  # However, I expect that chance of that happening to be negligible, so I make no attempts to address it.
  oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b'bc%d;' % uBreakpointId,
    sb0Comment = b'Remove breakpoint',
  );
  uAddress = oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId];
  oCdbWrapper.dauOldBreakpointAddresses_by_uProcessId.setdefault(uProcessId, []).append(uAddress);
  del oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
  del oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId];
  del oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
  oCdbWrapper.fbFireCallbacks("Log message", "Removed breakpoint", {
    "Breakpoint id": "%d" % uBreakpointId,
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
  });
