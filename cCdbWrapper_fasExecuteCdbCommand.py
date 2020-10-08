import re, threading, time;
from .cCdbStoppedException import cCdbStoppedException;
from .cEndOfCommandOutputMarkerMissingException import cEndOfCommandOutputMarkerMissingException;
from .dxConfig import dxConfig;

gbLogCommandExecutionTime = False;
gbDebugIO = False; # Used for debugging cdb I/O issues

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
    bShowOutputButNotCommandInHTMLReport = False, # Hide the command, but not its output
    bApplicationWillBeRun = False,
    bHandleSymbolLoadErrors = True,
    bIgnoreOutput = False,
    srIgnoredErrors = False,
    bUseMarkers = True,
    bRetryOnTruncatedOutput = False,
):
  assert isinstance(sCommand, str), \
      "sCommand must be a str, not %s" % repr(sCommand);
  assert sComment is None or isinstance(sComment, str), \
      "sComment must be a str, not %s" % repr(sComment);
  assert oCdbWrapper.oCdbStdInOutHelperThread.fbIsCurrentThread(), \
      "Commands can only be sent to cdb from within a cCdbWrapper.fCdbStdInOutHelperThread call.";
  if oCdbWrapper.bGenerateReportHTML:
    bAddCommandAndOutputToHTML = dxConfig["bShowAllCdbCommandsInReport"] or (bOutputIsInformative and dxConfig["bShowInformativeCdbCommandsInReport"]);
    if bAddCommandAndOutputToHTML:
      if gbLogCommandExecutionTime:
        nStartTimeInSeconds = time.clock();
      oCdbWrapper.sCdbIOHTML += "<hr/>\n";
      if not bShowOutputButNotCommandInHTMLReport:
        # Add the command and the prompt to the output:
        oCdbWrapper.sCdbIOHTML += oCdbWrapper.sPromptHTML + "<span class=\"CDBCommand\">%s</span>" % \
            oCdbWrapper.fsHTMLEncode(sCommand, uTabStop = 8);
        if sComment:
          # Optionally add the comment.
          oCdbWrapper.sCdbIOHTML += " <span class=\"CDBComment\">$ %s</span>" % oCdbWrapper.fsHTMLEncode(sComment);
        # End of line
        oCdbWrapper.sCdbIOHTML += "<br/>\n";
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
    oCdbWrapper.fbFireCallbacks("Cdb stdin input", sCommand);
    try:
      oCdbWrapper.oCdbConsoleProcess.oStdInPipe.fWriteBytes("%s\r\n" % sCommand);
    except IOError:
      oCdbWrapper.bCdbRunning = False;
      if gbDebugIO: print "\r>stdin:EOF>";
      assert oCdbWrapper.oCdbConsoleProcess.fbWait(), \
          "Could not wait for cdb.exe to terminate";
      oCdbWrapper.fbFireCallbacks("Log message", "Failed to write to cdb.exe stdin");
      raise cCdbStoppedException();
    try:
      if gbDebugIO: print ">stdin>%s" % sCommand;
      return oCdbWrapper.fasReadOutput(
        bOutputIsInformative = bOutputIsInformative,
        bApplicationWillBeRun = bApplicationWillBeRun,
        bHandleSymbolLoadErrors = bHandleSymbolLoadErrors,
        bIgnoreOutput = bIgnoreOutput,
        srIgnoredErrors = uTries == 1 and srIgnoredErrors or False, # Only ignore errors the last try.
        sStartOfCommandOutputMarker = bUseMarkers and sStartOfCommandOutputMarker or None,
        sEndOfCommandOutputMarker = bUseMarkers and sEndOfCommandOutputMarker or None,
      );
    except cEndOfCommandOutputMarkerMissingException as oEndOfCommandOutputMarkerMissingException:
      assert uTries > 1, \
          "End-of-command-output marker missing:\r\n%s" % "\r\n".join(oEndOfCommandOutputMarkerMissingException.asCommandOutput);
      uTries -= 1;
    finally:
      if oCdbWrapper.bGenerateReportHTML and bAddCommandAndOutputToHTML and gbLogCommandExecutionTime:
        nExecutionTimeInSeconds = time.clock() - nStartTimeInSeconds;
        oCdbWrapper.sCdbIOHTML += "Command executed in %.03f seconds.<br/>\n" % nExecutionTimeInSeconds;
      