import json, re;

def fExecuteCommands(oCdbWrapper, asCommands):
  for sCommand in asCommands:
    oCdbWrapper.fasExecuteCdbCommand(
      sCommand,
      "command embedded in application output",
      bOutputIsInformative = True,
      bUseMarkers = False,
    );

def fSetBreakpoints(oCdbWrapper, asBreakpointAddressses):
  asBreakpointsNotSetForAddresses = asBreakpointAddressses[:];
  for oProcess in oCdbWrapper.doProcess_by_uId.values():
    for sBreakpointAddress in asBreakpointAddressses:
      uBreakpointAddress = oProcess.fuGetValue(
        sValue = sBreakpointAddress,
        sComment = "Resolve breakpoint address",
      );
      if uBreakpointAddress:
        oProcess.fuAddBreakpoint(
          uAddress = uBreakpointAddress,
          fCallback = lambda uBreakpointId: (
            oCdbWrapper.fLogMessageInReport(
              "LogEmbeddedCommandsBreakpoint",
              "The application hit a breakpoint at %s in process %d/0x%X.\\r\\n" % (sBreakpointAddress, oProcess.uId, oProcess.uId),
            ),
          ), 
        );
        oCdbWrapper.fLogMessageInReport(
          "LogEmbeddedCommandsBreakpoint",
          "Added a breakpoint at %s in process %d/0x%X.\\r\\n" % (sBreakpointAddress, oProcess.uId, oProcess.uId),
        );
        if sBreakpointAddress in asBreakpointsNotSetForAddresses:
          asBreakpointsNotSetForAddresses.remove(sBreakpointAddress);
  for sBreakpointsNotSetForAddress in asBreakpointsNotSetForAddresses:
    oCdbWrapper.fLogMessageInReport(
      "LogEmbeddedCommandsBreakpoint",
      "Could not set any breakpoint at %s in any process." % sBreakpointsNotSetForAddress,
    );

def cCdbWrapper_fQueueCommandsEmbeddedInOutput(oCdbWrapper, sLine):
  oEmbeddedCommandsMatch = re.search(r"<<<cCdb:ExecuteCommands:JSON(\[.+?\])>>>", sLine);
  if oEmbeddedCommandsMatch:
    sEmbeddedCommandsJSON = oEmbeddedCommandsMatch.group(1);
    asEmbeddedCommands = json.loads(sEmbeddedCommandsJSON);
    oCdbWrapper.fInterrupt("Set breakpoints requested by embedded command", fExecuteCommands, oCdbWrapper, asEmbeddedCommands);
  oEmbeddedBreakpointsMatch = re.search(r"<<<cCdb:SetBreakpoints:JSON(\[.+?\])>>>", sLine);
  if oEmbeddedBreakpointsMatch:
    sEmbeddedBreakpointAddresssesJSON = oEmbeddedBreakpointsMatch.group(1);
    asEmbeddedBreakpointAddressses = json.loads(sEmbeddedBreakpointAddresssesJSON);
    oCdbWrapper.fInterrupt("Set breakpoints requested by embedded command", fSetBreakpoints, oCdbWrapper, asEmbeddedBreakpointAddressses);
