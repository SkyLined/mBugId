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

def cCdbWrapper_fasSendCommandAndReadOutput(oCdbWrapper, sCommand,
    bOutputIsInformative = False,
    bShowOnlyCommandOutput = False,
    bOutputCanContainApplicationOutput = False,
    bHandleSymbolLoadErrors = True,
    bIgnoreOutput = False,
    srIgnoreErrors = False,
    bUseMarkers = True,
):
  # Commands can only be execute from within the cCdbWrapper.fCdbStdInOutThread call.
  assert  threading.currentThread() == oCdbWrapper.oCdbStdInOutThread, \
      "Commands can only be sent to cdb from within a cCdbWrapper.fCdbStdInOutThread call.";
  if oCdbWrapper.bGenerateReportHTML:
    bAddCommandToHTML = oCdbWrapper.bGenerateReportHTML and (
      dxConfig["bShowAllCdbCommandsInReport"] or (
        (bOutputIsInformative and dxConfig["bShowInformativeCdbCommandsInReport"])
        and not bShowOnlyCommandOutput
      )
    ) 
  if bIgnoreOutput:
    bUseMarkers = False;
  elif bUseMarkers:
    sCommand = " ".join([s.rstrip(";") + ";" for s in [
      sPrintStartMarkerCommand, sCommand, sPrintEndMarkerCommand
    ]]);
  if dxConfig["bOutputStdIO"]:
    print "cdb<%s" % repr(sCommand)[1:-1];
  if oCdbWrapper.bGenerateReportHTML and not bIgnoreOutput:
    oCdbWrapper.sCdbIOHTML += "<hr/>";
    if bAddCommandToHTML:
      # Add the command to the current output block; this block should contain only one line that has the cdb prompt.
      oCdbWrapper.sCdbIOHTML += oCdbWrapper.sPromptHTML + "<span class=\"CDBCommand\">%s</span><br/>" % oCdbWrapper.fsHTMLEncode(sCommand, uTabStop = 8);
      oCdbWrapper.sPromptHTML = None;
  try:
    oCdbWrapper.oCdbProcess.stdin.write("%s\r\n" % sCommand);
  except Exception, oException:
    oCdbWrapper.bCdbRunning = False;
    raise cCdbStoppedException();
  # The following command will always add a new output block with the new cdb prompt, regardless of bDoNotSaveIO.
  return oCdbWrapper.fasReadOutput(
    bOutputIsInformative = bOutputIsInformative,
    bOutputCanContainApplicationOutput = bOutputCanContainApplicationOutput,
    bHandleSymbolLoadErrors = bHandleSymbolLoadErrors,
    bIgnoreOutput = bIgnoreOutput,
    srIgnoreErrors = srIgnoreErrors,
    sStartOfCommandOutputMarker = bUseMarkers and sStartOfCommandOutputMarker or None,
    sEndOfCommandOutputMarker = bUseMarkers and sEndOfCommandOutputMarker or None,
  );
