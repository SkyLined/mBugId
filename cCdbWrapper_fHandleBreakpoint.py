def cCdbWrapper_fHandleBreakpoint(oCdbWrapper, uBreakpointId):
  # A breakpoint was hit; sanity checks, log message and fire the callback
  uExpectedProcessId = oCdbWrapper.duProcessId_by_uBreakpointId[uBreakpointId];
  assert oCdbWrapper.oCdbCurrentProcess.uId == uExpectedProcessId, \
      "Breakpoint #%d was set in process 0x%X but reported to have been hit in process 0x%X!?" % \
      (uBreakpointId, uExpectedProcessId, oCdbWrapper.oCdbCurrentProcess.uId);
  uBreakpointAddress = oCdbWrapper.duAddress_by_uBreakpointId[uBreakpointId];
  # We could sanity check the breakpoint address matched current eip/rip, but I don't have time to implement it and
  # it would slow things down a bit.
  oCdbWrapper.fbFireCallbacks("Log message", "Breakpoint hit", {
    "Process": "0x%X" % (uExpectedProcessId,),
    "Breakpoint id": "%d" % (uBreakpointId,),
    "Address": "0x%X" % (uBreakpointAddress,),
  });
  fBreakpointCallback = oCdbWrapper.dfCallback_by_uBreakpointId[uBreakpointId];
  fBreakpointCallback(uBreakpointId);
