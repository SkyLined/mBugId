import re, threading, time;

from mNotProvided import *;
from .cCdbStoppedException import cCdbStoppedException;
from .cEndOfCommandOutputMarkerMissingException import cEndOfCommandOutputMarkerMissingException;
from .dxConfig import dxConfig;
from .mCP437 import fsCP437FromBytesString, fsCP437HTMLFromBytesString;

gbLogCommandExecutionTime = False;
gbDebugIO = False; # Used for debugging cdb I/O issues

# It appears cdb can sometimes buffer output from the application and output it after the prompt is shown. This would
# cause this application output to be treated as part of the output of whatever command we are trying to execute if we
# don't handle such situations. The solutions I employ is to add two commands before and after the actual command that
# output markers that we can detect. These markers can be used to ignore output that is not part of the output for the
# command.
gsbStartOfCommandOutputMarker = b"<\x01[\x02{";
gsbEndOfCommandOutputMarker = b"}\x02]\x01>";
# The command that outputs the marker should not contain the marker itself: any cdb output that echos the command would
# otherwise output the marker and may lead to incorrect parsing of data. This encodes the marker in the command:
def fsbCreatePrintMarkerCommand(sbMarker):
  return b'.printf "%s\\r\\n", %s;' % (
    b"%c" * len(sbMarker),
    b", ".join([b"0x%X" % uByte for uByte in sbMarker])
  );
gsbPrintStartMarkerCommand = fsbCreatePrintMarkerCommand(gsbStartOfCommandOutputMarker);
gsbPrintEndMarkerCommand = fsbCreatePrintMarkerCommand(gsbEndOfCommandOutputMarker);

def cCdbWrapper_fasbExecuteCdbCommand(oCdbWrapper,
    sbCommand,
    sb0Comment,
    bOutputIsInformative = False,
    bShowOutputButNotCommandInHTMLReport = False, # Hide the command, but not its output
    bApplicationWillBeRun = False,
    bHandleSymbolLoadErrors = True,
    bIgnoreOutput = False,
    rb0IgnoredErrors = None,
    bUseMarkers = True,
    bRetryOnTruncatedOutput = False,
):
  fAssertType("sbCommand", sbCommand, bytes);
  fAssertType("sb0Comment", sb0Comment, bytes, None);
  assert oCdbWrapper.oCdbStdInOutHelperThread.fbIsCurrentThread(), \
      "Commands can only be sent to cdb from within a cCdbWrapper.fCdbStdInOutHelperThread call.";
  if oCdbWrapper.bGenerateReportHTML:
    bAddCommandAndOutputToHTML = dxConfig["bShowAllCdbCommandsInReport"] or (bOutputIsInformative and dxConfig["bShowInformativeCdbCommandsInReport"]);
    if bAddCommandAndOutputToHTML:
      if gbLogCommandExecutionTime:
        nStartTimeInSeconds = time.time();
      oCdbWrapper.sCdbIOHTML += "<hr/>\n";
      if not bShowOutputButNotCommandInHTMLReport:
        # Add the command and the prompt to the output:
        oCdbWrapper.sCdbIOHTML += oCdbWrapper.sPromptHTML + "<span class=\"CDBCommand\">%s</span>" % (
          fsCP437HTMLFromBytesString(sbCommand, u0TabStop = 8),
        );
        if sb0Comment:
          # Optionally add the comment.
          oCdbWrapper.sCdbIOHTML += " <span class=\"CDBComment\">$ %s</span>" % (
            fsCP437HTMLFromBytesString(sb0Comment),
          );
        # End of line
        oCdbWrapper.sCdbIOHTML += "<br/>\n";
    oCdbWrapper.sPromptHTML = None; # We expect a new prompt.
  if bIgnoreOutput:
    bUseMarkers = False;
  elif bUseMarkers:
    sbCommand = b"%s .block{ %s }; %s%s" % (
      gsbPrintStartMarkerCommand,
      sbCommand,
      gsbPrintEndMarkerCommand,
      sb0Comment and (b" $$ %s" % sb0Comment) or b"",
    );
  uTries = bRetryOnTruncatedOutput and 5 or 1; # It seems that one retry may not be enough... :(
  while 1:
    oCdbWrapper.fbFireCallbacks("Cdb stdin input", sbCommand);
    try:
      oCdbWrapper.oCdbConsoleProcess.oStdInPipe.fWriteBytes(sbCommand + b"\r\n");
    except IOError:
      oCdbWrapper.bCdbIsRunning = False;
      if gbDebugIO: print("\r>stdin:EOF>");
      assert oCdbWrapper.oCdbConsoleProcess.fbWait(), \
          "Could not wait for cdb.exe to terminate";
      oCdbWrapper.fbFireCallbacks("Log message", "Failed to write to cdb.exe stdin");
      raise cCdbStoppedException();
    try:
      if gbDebugIO: print(">stdin>%s" % fsCP437FromBytesString(sbCommand));
      return oCdbWrapper.fasbReadOutput(
        bOutputIsInformative = bOutputIsInformative,
        bApplicationWillBeRun = bApplicationWillBeRun,
        bHandleSymbolLoadErrors = bHandleSymbolLoadErrors,
        bIgnoreOutput = bIgnoreOutput,
        rb0IgnoredErrors = rb0IgnoredErrors if uTries == 1 else None, # Only ignore errors the last try.
        sb0StartOfCommandOutputMarker = bUseMarkers and gsbStartOfCommandOutputMarker or None,
        sb0EndOfCommandOutputMarker = bUseMarkers and gsbEndOfCommandOutputMarker or None,
      );
    except cEndOfCommandOutputMarkerMissingException as oEndOfCommandOutputMarkerMissingException:
      uTries -= 1;
      if uTries == 0:
        raise;
    finally:
      if oCdbWrapper.bGenerateReportHTML and bAddCommandAndOutputToHTML and gbLogCommandExecutionTime:
        nExecutionTimeInSeconds = time.time() - nStartTimeInSeconds;
        oCdbWrapper.sCdbIOHTML += "Command executed in %.03f seconds.<br/>\n" % nExecutionTimeInSeconds;
      