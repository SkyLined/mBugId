import re, threading;
from cCdbStoppedException import cCdbStoppedException;
from dxConfig import dxConfig;

# It appears cdb can sometimes buffer output from the application and output it after the prompt is shown. This would
# cause this application output to be treated as part of the output of whatever command we are trying to execute if we
# don't handle such situations. The solutions I employ is to add two commands before and after the actual command that
# output markers that we can detect. These markers can be used to ignore output that is not part of the output for the
# command.
sStartOfCommandOutputMarker = "<\x01[\x02{";
sEndOfCommandOutputMarker = "}\x02]\x01>";
# The command that outputs the marker should not contain the marker itself: any cdb output that echos the command would
# otherwise output the marker and may lead to incorrect parsing of data. This encodes the marker in the command:
sPrintStartMarkerCommand ='.printf "%s\\r\\n", %s;' % ("%c" * len(sStartOfCommandOutputMarker), ", ".join(["0x%X" % ord(s) for s in sStartOfCommandOutputMarker]));
sPrintEndMarkerCommand ='.printf "%s\\r\\n", %s;' % ("%c" * len(sEndOfCommandOutputMarker), ", ".join(["0x%X" % ord(s) for s in sEndOfCommandOutputMarker]));

def cCdbWrapper_fasExecuteCdbCommand(oCdbWrapper,
    sCommand,
    sComment,
    bOutputIsInformative = False,
    bShowCommandInHTMLReport = True,
    bOutputCanContainApplicationOutput = False,
    bHandleSymbolLoadErrors = True,
    bIgnoreOutput = False,
    srIgnoreErrors = False,
    bUseMarkers = True,
    bRetryOnTruncatedOutput = False,
):
  # Commands can only be execute from within the cCdbWrapper.fCdbStdInOutThread call.
  assert  threading.currentThread() == oCdbWrapper.oCdbStdInOutThread, \
      "Commands can only be sent to cdb from within a cCdbWrapper.fCdbStdInOutThread call.";
  if oCdbWrapper.bGenerateReportHTML:
    bAddCommandToHTML = (
      bShowCommandInHTMLReport # Always show
      or (bOutputIsInformative and dxConfig["bShowInformativeCdbCommandsInReport"]) # Show if the user requests these
      or dxConfig["bShowAllCdbCommandsInReport"] # Show if the user requests all
    ) 
    if bAddCommandToHTML or not bIgnoreOutput:
      oCdbWrapper.sCdbIOHTML += "<hr/>";
    if bAddCommandToHTML:
      # Add the command and the prompt to the output:
      oCdbWrapper.sCdbIOHTML += oCdbWrapper.sPromptHTML + "<span class=\"CDBCommand\">%s</span><br/>" % oCdbWrapper.fsHTMLEncode(sCommand, uTabStop = 8);
    oCdbWrapper.sPromptHTML = None; # We expect a new prompt.
  if bIgnoreOutput:
    bUseMarkers = False;
  elif bUseMarkers:
    sCommand = "%s .block{ %s }; %s%s" % (
      sPrintStartMarkerCommand,
      sCommand,
      sPrintEndMarkerCommand,
      sComment and (" $$ %s" % sComment) or "",
    );
  uTries = bRetryOnTruncatedOutput and 5 or 1; # It seems that one retry may not be enough... :(
  while uTries:
    if dxConfig["bOutputStdIO"]:
      print "cdb<%s" % repr(sCommand)[1:-1];
    try:
      oCdbWrapper.oCdbProcess.stdin.write("%s\r\n" % sCommand);
    except Exception, oException:
      oCdbWrapper.bCdbRunning = False;
      raise cCdbStoppedException();
    asOutput = oCdbWrapper.fasReadOutput(
      bOutputIsInformative = bOutputIsInformative,
      bOutputCanContainApplicationOutput = bOutputCanContainApplicationOutput,
      bHandleSymbolLoadErrors = bHandleSymbolLoadErrors,
      bIgnoreOutput = bIgnoreOutput,
      srIgnoreErrors = uTries == 1 and srIgnoreErrors or False, # Only ignore errors the last try.
      sStartOfCommandOutputMarker = bUseMarkers and sStartOfCommandOutputMarker or None,
      sEndOfCommandOutputMarker = bUseMarkers and sEndOfCommandOutputMarker or None,
      bDontAssertOnTruncatedOutput = uTries > 1,
    );
    if asOutput is not None:
      break; # No retries needed; it already succeeded.
    uTries -= 1;
  return asOutput;
