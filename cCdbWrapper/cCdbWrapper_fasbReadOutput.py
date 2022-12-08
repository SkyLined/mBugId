import re;

from ..dxConfig import dxConfig;
from ..mCP437 import fsCP437FromBytesString, fsCP437HTMLFromBytesString;

gbDebugIO = False; # Used for debugging cdb I/O issues

gdsTips_by_sbErrorMessage = {
  b"Win32 error 0n2": "\r\n".join([
    "- You may have provided an incorrect path to the executable."
  ]),
  b"Win32 error 0n5": "\r\n".join([
    "- You may have provided an incorrect path to the executable,"
    "- you may not have the required permissions to read and/or execute the executable,"
    "- you may need to run as an administrator."
  ]),
  b"NTSTATUS 0xC00000BB": "\r\n".join([
    "- You may be trying to debug a 64-bit process with a 64-bit debugger.",
  ]),
  b"NTSTATUS 0xC000010A": "\r\n".join([
    "- The process appears to have terminated right before the debugger could attach."
  ]),
};

# This will be output right in the middle of a line. Luckily it ends with a CRLF, so we can remove it from
# the output and reconstruct the line as it would have been without this cruft.
grbLineInterruptedByCdbError = re.compile(
  rb"\A"
  rb"(.*?)"
  rb"("
    rb"(?:\*\*\* )?"
    rb"(?:ERROR|WARNING|DBGHELP): "
    rb"(?:" + (rb"|".join([
      rb"Module load completed but symbols could not be loaded for .*",
      rb"Symbol file could not be found\.  Defaulted to export symbols for .*",
      rb"Frame IP not in any known module\. Following frames may be wrong\.",
      rb"Stack overflow detected\. The unwound frames are extracted from outside normal stack bounds\.",
      rb"Stack pointer is outside the normal stack bounds\. Stack unwinding can be inaccurate\.",
      rb"Stack unwind information not available\. Following frames may be wrong\.",
      rb"Unable to verify checksum for .*",
      rb"The debugger does not have a current process or thread",
      rb"Many commands will not work",
      rb"(?:.+) (?:\- E_PDB_CORRUPT|dia error 0x[0-9a-f]+)"
    ])) + rb")"
  rb")"
  rb"\s*\Z"
);

# The prompt normally contains pid and tid information, but for unknown reasons
# cdb can get confused about which process it is debugging and show "?:???>"
grbCdbPrompt = re.compile(
  rb"\A"
  rb"(?:\d+|\?)"      # pid or "?"
  rb":"               # ":"
  rb"(?:\d+|\?\?\?)"  # tid or "???"
  rb"(:x86)?"         # optional { ":x86" }
  rb"> "              # "> "
  rb"\Z");
grbEventFailedError = re.compile(
  rb"\A"
  rb"(ERROR: )?"
  rb"(\w+Event) failed, "
  rb"(NTSTATUS 0x[0-9a-fA-F])"
  rb"\s*\Z"
);
grbFirstChanceCPPException = re.compile(
  rb"\A"
  rb"\(\w+\.\w+\): C\+\+ EH exception \- code \w+ \(first chance\)"
  rb"\s*\Z"
);

def cCdbWrapper_fasbReadOutput(oCdbWrapper,
  bOutputIsInformative = False,
  bApplicationWillBeRun = False,
  bIgnoreOutput = False,
  sb0StartOfCommandOutputMarker = None, # Every command is preceded and followed by commands that outputs marker strings.
  sb0EndOfCommandOutputMarker = None,   # These are used to detect where the output of the cdb command starts in cases
                                       # where the application has output something out of sync. The applications output
                                       # should either precede or follow the command output markers. This allowing us
                                       # to ignore the application output and only return the command output to the
                                       # caller.
):
  if bIgnoreOutput:
    bAddOutputToHTMLReport = oCdbWrapper.bGenerateReportHTML and dxConfig["bShowAllCdbCommandsInReport"];
  else:
    if sb0StartOfCommandOutputMarker:
      assert sb0EndOfCommandOutputMarker, \
          "sb0StartOfCommandOutputMarker requires sb0EndOfCommandOutputMarker";
    else:
      assert not sb0EndOfCommandOutputMarker, \
          "sb0EndOfCommandOutputMarker requires sb0StartOfCommandOutputMarker";
    bAddOutputToHTMLReport = oCdbWrapper.bGenerateReportHTML and (
      dxConfig["bShowAllCdbCommandsInReport"]
      or (bOutputIsInformative and dxConfig["bShowInformativeCdbCommandsInReport"])
      or bApplicationWillBeRun
    );
  bStartOfCommandOutputMarkerFound = False;
  bEndOfCommandOutputMarkerFound = False;
  sbCurrentLine = b"";
  sbFilteredCurrentLine = b"";
  asbFilteredLines = [];
  if bApplicationWillBeRun:
    # Signal that the application is running and start the interrupt on timeout thread.
    oCdbWrapper.bApplicationIsRunning = True;
    oCdbWrapper.oInterruptOnTimeoutHelperThread.fStart();
  try: # "try:" because the oInterruptOnTimeoutHelperThread needs to be stopped in a "finally:" if there is an exception.
    while 1:
      u0Byte = oCdbWrapper.oCdbConsoleProcess.oStdOutPipe.fu0ReadByte(); # returns None if pipe is closed.
      if u0Byte == 0x0D: # CR
        assert not bEndOfCommandOutputMarkerFound, \
            "CR after end of command output marker in %s!?" % repr(sbCurrentLine);
        pass; # ignored.
      elif u0Byte is None or u0Byte == 0x0A: # EOF or LF
        if gbDebugIO: print("\r<stdout>%s" % str(sbFilteredCurrentLine, "cp437", "strict"));
        assert u0Byte is None or not bEndOfCommandOutputMarkerFound, \
            "LF after end of command output marker in %s!?" % repr(sbCurrentLine);
        o0LineInterruptedByCdbError = re.match(grbLineInterruptedByCdbError, sbFilteredCurrentLine);
        if o0LineInterruptedByCdbError:
          # Remove the error message from this line and pretend that it was output before this line:
          sbFilteredCurrentLine, sbErrorMessage = o0LineInterruptedByCdbError.groups();
          if bAddOutputToHTMLReport:
            sLineHTML = "<span class=\"CDBStdOut\">%s</span><br/>\n" % \
                (fsCP437HTMLFromBytesString(sbErrorMessage, u0TabStop = 8));
            # Add the line to the current block of I/O
            oCdbWrapper.sCdbIOHTML += sLineHTML;
          # We will continue to append to the current line, now without the inject error message.
        elif sbFilteredCurrentLine:
          oCdbWrapper.fbFireCallbacks("Cdb stdout output", sbFilteredCurrentLine);
          # Failure to debug application must be special cased, for example:
          # |ERROR: ContinueEvent failed, NTSTATUS 0xC000000D
          # |WaitForEvent failed, NTSTATUS 0xC000000D
          oEventFailedMatch = grbEventFailedError.match(sbFilteredCurrentLine);
          if oEventFailedMatch:
            sEventName, sErrorMessage = oEventFailedMatch.groups();
            sErrorReport = "Failed to debug process: %s failed with %s" % (sEventName, sErrorMessage);
            if sErrorMessage in gdsTips_by_sbErrorMessage:
              sErrorReport += "\r\n" + gdsTips_by_sbErrorMessage[sErrorMessage];
            assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sErrorReport), \
                sErrorReport;
            oCdbWrapper.fStop();
          if grbFirstChanceCPPException.match(sbFilteredCurrentLine):
            # I cannot figure out how to detect second chance C++ exceptions without cdb outputting a line every time a
            # first chance C++ exception happens. These lines are clutter and MSIE outputs a lot of them, so they are
            # ignored here. TODO: find a way to break on second chance exceptions without getting a report about first
            # chance exceptions.
            pass;
          else:
            if bAddOutputToHTMLReport:
              sClass = bApplicationWillBeRun and "CDBOrApplicationStdOut" or "CDBCommandResult";
              sLineHTML = "<span class=\"%s\">%s</span><br/>\n" % \
                  (sClass, fsCP437HTMLFromBytesString(sbFilteredCurrentLine, u0TabStop = 8));
              # Add the line to the current block of I/O
              oCdbWrapper.sCdbIOHTML += sLineHTML;
            if bApplicationWillBeRun:
              oCdbWrapper.fbFireCallbacks("Log message", "StdOut output", {
                "Line": sbFilteredCurrentLine,
              });
            asbFilteredLines.append(sbFilteredCurrentLine);
          sbFilteredCurrentLine = b"";
        if u0Byte is None:
          oCdbWrapper.bCdbIsRunning = False;
          if gbDebugIO: print("<stdout:EOF>");
          oCdbWrapper.fbFireCallbacks("Log message", "Failed to read from cdb.exe stdout");
          raise oCdbWrapper.cCdbStoppedException();
        sbCurrentLine = b"";
      else:
        sbCurrentLine += bytes((u0Byte,));
        sbFilteredCurrentLine += bytes((u0Byte,));
        if gbDebugIO: print("\r<stdout~%s" % str(sbFilteredCurrentLine, "cp437", "strict"), end = "\r");
        if not bIgnoreOutput:
          # Detect cdb warnings and errors:
          o0LineInterruptedByCdbError = re.match(grbLineInterruptedByCdbError, sbFilteredCurrentLine);
          if not o0LineInterruptedByCdbError:
            if sb0StartOfCommandOutputMarker and not bStartOfCommandOutputMarkerFound:
              if sbFilteredCurrentLine == sb0StartOfCommandOutputMarker:
                if gbDebugIO: print("\r<stdout:START>%s" % str(sbFilteredCurrentLine, "cp437", "strict"));
                bStartOfCommandOutputMarkerFound = True;
                sbFilteredCurrentLine = b"";
              else:
                assert len(sbFilteredCurrentLine) < len(sb0StartOfCommandOutputMarker), \
                    "Command output does not start with marker %s: %s" % \
                    (repr(sb0StartOfCommandOutputMarker), repr(sbCurrentLine));
            if sb0EndOfCommandOutputMarker and not bEndOfCommandOutputMarkerFound:
              if sbFilteredCurrentLine.endswith(sb0EndOfCommandOutputMarker):
                if gbDebugIO: print("\r<stdout:END>%s" % str(sbFilteredCurrentLine, "cp437", "strict"));
                bEndOfCommandOutputMarkerFound = True;
                sbFilteredCurrentLine = sbFilteredCurrentLine[:-len(sb0EndOfCommandOutputMarker)];
        # Detect the prompt. The prompt must starts on a new line (but can be prefixed with the
        # end of command output marker).
        oPromptMatch = grbCdbPrompt.match(sbFilteredCurrentLine);
        if oPromptMatch:
          oCdbWrapper.sCdbCurrentISA = oPromptMatch.group(1) and "x86" or oCdbWrapper.sCdbISA;
          if oCdbWrapper.bGenerateReportHTML:
            # The prompt is always stored in a new block of I/O
            oCdbWrapper.sPromptHTML = "<span class=\"CDBPrompt\">%s</span>" % fsCP437HTMLFromBytesString(sbCurrentLine);
          oCdbWrapper.fbFireCallbacks("Cdb stdout output", sbCurrentLine);
          if not bIgnoreOutput:
            if sb0EndOfCommandOutputMarker is not None and not bEndOfCommandOutputMarkerFound:
              raise oCdbWrapper.cEndOfCommandOutputMarkerMissingException(asbFilteredLines);
          break;
  finally:
    if bApplicationWillBeRun:
      # Signal that the application is no longer running and wait for the interrupt on timeout thread to stop.
      oCdbWrapper.bApplicationIsRunning = False;
      oCdbWrapper.oInterruptOnTimeoutHelperThread.fWait();
  return None if bIgnoreOutput else asbFilteredLines;
