import json, re;

def fExecuteCommands(oCdbWrapper, asCommands):
  for sCommand in asCommands:
    oCdbWrapper.fasExecuteCdbCommand(
      sCommand,
      "command embedded in application output",
      bOutputIsInformative = True,
      bShowCommandInHTMLReport = True,
      bUseMarkers = False,
    );

def fSetBreakpoints(oCdbWrapper, asBreakpointAddressses):
  for oProcess in oCdbWrapper.doProcess_by_uId.values():
    for sBreakpointAddresss in asBreakpointAddressses:
      uBreakpointAddress = oProcess.fuGetValue(
        sValueName = sBreakpointAddresss,
        sComment = "Resolve breakpoint address",
      );
      if uBreakpointAddress:
        oProcess.fuAddBreakpoint(
          uAddress = uBreakpointAddress,
          fCallback = lambda uBreakpointId: (
            oCdbWrapper.fasExecuteCdbCommand(
              sCommand = '.printf "The application hit a breakpoint at %s in process %d/0x%X.\\r\\n";' % (sBreakpointAddresss, oProcess.uId, oProcess.uId),
              sComment = None,
              bShowCommandInHTMLReport = False,
              bRetryOnTruncatedOutput = True,
            ),
          ), 
        );
        oCdbWrapper.fasExecuteCdbCommand(
          sCommand = '.printf "Added a breakpoint at %s in process %d/0x%X.\\r\\n";' % (sBreakpointAddresss, oProcess.uId, oProcess.uId),
          sComment = None,
          bShowCommandInHTMLReport = False,
          bRetryOnTruncatedOutput = True,
        );
      else:
        oCdbWrapper.fasExecuteCdbCommand(
          sCommand = '.printf "Could not set a breakpoint at %s (unknown symbol) in process %d/0%X.\\r\\n";' % (sBreakpointAddresss, oProcess.uId, oProcess.uId),
          sComment = None,
          bShowCommandInHTMLReport = False,
          bRetryOnTruncatedOutput = True,
        );

def cCdbWrapper_fQueueCommandsEmbeddedInOutput(oCdbWrapper, sLine):
  oEmbeddedCommandsMatch = re.search(r"<<<cCdb:ExecuteCommands:JSON(\[.+?\])>>>", sLine);
  if oEmbeddedCommandsMatch:
    sEmbeddedCommandsJSON = oEmbeddedCommandsMatch.group(1);
    asEmbeddedCommands = json.loads(sEmbeddedCommandsJSON);
    oCdbWrapper.fInterrupt(fExecuteCommands, oCdbWrapper, asEmbeddedCommands);
  oEmbeddedBreakpointsMatch = re.search(r"<<<cCdb:SetBreakpoints:JSON(\[.+?\])>>>", sLine);
  if oEmbeddedBreakpointsMatch:
    sEmbeddedBreakpointAddresssesJSON = oEmbeddedBreakpointsMatch.group(1);
    asEmbeddedBreakpointAddressses = json.loads(sEmbeddedBreakpointAddresssesJSON);
    oCdbWrapper.fInterrupt(fSetBreakpoints, oCdbWrapper, asEmbeddedBreakpointAddressses);
