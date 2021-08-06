import re;
from .cCdbStoppedException import cCdbStoppedException;
from .cEndOfCommandOutputMarkerMissingException import cEndOfCommandOutputMarkerMissingException;
from .cHelperThread import cHelperThread;
from .dxConfig import dxConfig;

from mFileSystemItem import cFileSystemItem;

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
grbAlwaysIgnoredCdbOutputLine = re.compile(rb"^(.*?)((?:\*\*\* )?(?:%s))$" % rb"|".join([
  rb"ERROR: Module load completed but symbols could not be loaded for .*",
  rb"ERROR: Symbol file could not be found.  Defaulted to export symbols for .*",
  rb"WARNING: Frame IP not in any known module\. Following frames may be wrong\.",
  rb"WARNING: Stack overflow detected\. The unwound frames are extracted from outside normal stack bounds\.",
  rb"WARNING: Stack pointer is outside the normal stack bounds\. Stack unwinding can be inaccurate\.",
  rb"WARNING: Stack unwind information not available\. Following frames may be wrong\.",
  rb"WARNING: Unable to verify checksum for .*",
  rb"WARNING: The debugger does not have a current process or thread",
  rb"WARNING: Many commands will not work",
]));

grbBadPDBError = re.compile(rb"^DBGHELP: (.+) (?:\- E_PDB_CORRUPT|dia error 0x[0-9a-f]+)\s*$");
grbCdbPrompt = re.compile(rb"^(?:\d+|\?):(?:\d+|\?\?\?)(:x86)?> $");
grbEventFailedError = re.compile(rb"^(ERROR: )?(\w+Event) failed, (NTSTATUS 0x[0-9a-fA-F])$");
grbFailedToLoadSymbolsError = re.compile(rb"^\*\*\* ERROR: Module load completed but symbols could not be loaded for (?:.*\\)*([^\\]+)");
grbFirstChanceCPPException = re.compile(rb"^\(\w+\.\w+\): C\+\+ EH exception \- code \w+ \(first chance\)\s*$");
grbSymbolLoadError = re.compile(rb"\*\*\* ERROR: Symbol file could not be found\.  Defaulted to export symbols for .*$");

def cCdbWrapper_fasbReadOutput(oCdbWrapper,
  bOutputIsInformative = False,
  bApplicationWillBeRun = False,
  bHandleSymbolLoadErrors = True,
  bIgnoreOutput = False,
  rb0IgnoredErrors = None,
  sb0StartOfCommandOutputMarker = None, # Every command is preceded and followed by commands that outputs marker strings.
  sb0EndOfCommandOutputMarker = None,   # These are used to detect where the output of the cdb command starts in cases
                                       # where the application has output something out of sync. The applications output
                                       # should either precede or follow the command output markers. This allowing us
                                       # to ignore the application output and only return the command output to the
                                       # caller.
):
  if bIgnoreOutput:
    bAddOutputToHTMLReport = oCdbWrapper.bGenerateReportHTML and dxConfig["bShowAllCdbCommandsInReport"];
    sb0IgnoredLine = b"";
  else:
    asbReturnedLines = [];
    if sb0StartOfCommandOutputMarker:
      assert sb0EndOfCommandOutputMarker, \
          "sb0StartOfCommandOutputMarker requires sb0EndOfCommandOutputMarker";
      sb0ReturnedLine = None;
      sb0IgnoredLine = b"";
    else:
      assert not sb0EndOfCommandOutputMarker, \
          "sb0EndOfCommandOutputMarker requires sb0StartOfCommandOutputMarker";
      sb0ReturnedLine = b"";
      sb0IgnoredLine = None;
    bAddOutputToHTMLReport = oCdbWrapper.bGenerateReportHTML and (
      dxConfig["bShowAllCdbCommandsInReport"]
      or (bOutputIsInformative and dxConfig["bShowInformativeCdbCommandsInReport"])
      or bApplicationWillBeRun
    );
  sbLine = b"";
  asbLines = [];
  if bApplicationWillBeRun:
    # Signal that the application is running and start the interrupt on timeout thread.
    oCdbWrapper.bApplicationIsRunning = True;
    oCdbWrapper.oInterruptOnTimeoutHelperThread.fStart();
  try: # "try:" because the oInterruptOnTimeoutHelperThread needs to be stopped in a "finally:" if there is an exception.
    bConcatinateReturnedLineToNext = False;
    while 1:
      u0Byte = oCdbWrapper.oCdbConsoleProcess.oStdOutPipe.fu0ReadByte(); # return "" if pipe is closed.
      if u0Byte == 0x0D: # CR
        pass; # ignored.
      elif u0Byte is None or u0Byte == 0x0A:
        if gbDebugIO: print("\r<stdout<%s" % sbLine);
        if u0Byte == 0x0A or sbLine:
          oCdbWrapper.fbFireCallbacks("Cdb stdout output", sbLine);
          # Failure to debug application must be special cased, for example:
          # |ERROR: ContinueEvent failed, NTSTATUS 0xC000000D
          # |WaitForEvent failed, NTSTATUS 0xC000000D
          oEventFailedMatch = grbEventFailedError.match(sbLine);
          if oEventFailedMatch:
            sEventName, sErrorMessage = oEventFailedMatch.groups();
            sErrorReport = "Failed to debug process: %s failed with %s" % (sEventName, sErrorCode);
            if sErrorMessage in gdsTips_by_sbErrorMessage:
              sErrorReport += "\r\n" + gdsTips_by_sbErrorMessage[sErrorCode];
            assert oCdbWrapper.fbFireCallbacks("Failed to debug application", sErrorReport), \
                sErrorReport;
            oCdbWrapper.fStop();
          bConcatinateReturnedLineToNext = False;
          if grbFirstChanceCPPException.match(sbLine):
            # I cannot figure out how to detect second chance C++ exceptions without cdb outputting a line every time a
            # first chance C++ exception happens. These lines are clutter and MSIE outputs a lot of them, so they are
            # ignored here. TODO: find a way to break on second chance exceptions without getting a report about first
            # chance exceptions.
            pass; 
          else:
            asbLines.append(sbLine);
            # Strip useless symbol warnings and errors:
            if sb0IgnoredLine is not None:
              bStartOfCommandOutput = (
                False if bIgnoreOutput else
                sb0IgnoredLine.endswith(sb0StartOfCommandOutputMarker) if sb0StartOfCommandOutputMarker else
                False
              );
              if bStartOfCommandOutput:
                sb0IgnoredLine = sb0IgnoredLine[:-len(sb0StartOfCommandOutputMarker)]; # Remove the marker from the line;
              if len(sb0IgnoredLine) > 0:
                if bAddOutputToHTMLReport:
                  sClass = bApplicationWillBeRun and "CDBOrApplicationStdOut" or "CDBStdOut";
                  sLineHTML = "<span class=\"%s\">%s</span><br/>\n" % (sClass, oCdbWrapper.fsHTMLEncode(sb0IgnoredLine, uTabStop = 8));
                  # Add the line to the current block of I/O
                  oCdbWrapper.sCdbIOHTML += sLineHTML;
                if bApplicationWillBeRun:
                  oCdbWrapper.fbFireCallbacks("Log message", "StdOut output", {
                    "Line": sb0IgnoredLine,
                  });
              if bStartOfCommandOutput:
                sb0ReturnedLine = b""; # Start collecting lines to return to the caller.
                sb0IgnoredLine = None; # Stop ignoring lines
                sb0StartOfCommandOutputMarker = None; # Stop looking for the marker.
            else:
              oIgnoredCdbOutputLine = grbAlwaysIgnoredCdbOutputLine.match(sb0ReturnedLine);
              if oIgnoredCdbOutputLine:
                # Some cruft got injected into the line; remove it and pretend that it was output before the line:
                sb0ReturnedLine, sbCruft = oIgnoredCdbOutputLine.groups();
                if bAddOutputToHTMLReport:
                  sLineHTML = "<span class=\"CDBStdOut\">%s</span><br/>\n" % (oCdbWrapper.fsHTMLEncode(sbCruft, uTabStop = 8));
                  # Add the line to the current block of I/O
                  oCdbWrapper.sCdbIOHTML += sLineHTML;
                # Ignore this CRLF, as it was injected by the cruft, so we need to reconstruct the intended line from
                # this line and the next line:
                bConcatinateReturnedLineToNext = True;
                bEndOfCommandOutput = False;
              else:
                bEndOfCommandOutput = sb0ReturnedLine.endswith(sb0EndOfCommandOutputMarker) if sb0EndOfCommandOutputMarker else False;
                if bEndOfCommandOutput:
                  sb0ReturnedLine = sb0ReturnedLine[:-len(sb0EndOfCommandOutputMarker)]; # Remove the marker from the line;
                if sb0ReturnedLine:
                  if bAddOutputToHTMLReport:
                    sClass = bApplicationWillBeRun and "CDBOrApplicationStdOut" or "CDBCommandResult";
                    sLineHTML = "<span class=\"%s\">%s</span><br/>\n" % (sClass, oCdbWrapper.fsHTMLEncode(sb0ReturnedLine, uTabStop = 8));
                    # Add the line to the current block of I/O
                    oCdbWrapper.sCdbIOHTML += sLineHTML;
                  if bApplicationWillBeRun:
                    oCdbWrapper.fbFireCallbacks("Log message", "StdOut output", {
                      "Line": sb0ReturnedLine,
                    });
                  asbReturnedLines.append(sb0ReturnedLine);
              if bEndOfCommandOutput:
                sb0EndOfCommandOutputMarker = None; # Stop looking for the marker.
                sb0ReturnedLine = None; # Stop collecting lines to return to the caller.
                sb0IgnoredLine = b""; # Start ignoring lines
        if u0Byte is None:
          oCdbWrapper.bCdbIsRunning = False;
          if gbDebugIO: print("<stdout:EOF<");
          oCdbWrapper.fbFireCallbacks("Log message", "Failed to read from cdb.exe stdout");
          raise cCdbStoppedException();
        sbLine = b"";
        if sb0IgnoredLine is not None:
          sb0IgnoredLine = b"";
        elif not bConcatinateReturnedLineToNext:
          sb0ReturnedLine = b"";
      else:
        sbLine += bytes((u0Byte,));
        if gbDebugIO: print("\r<stdout<%s" % str(sbLine, 'latin1'), end=' ');
        if sb0IgnoredLine is None:
          sb0ReturnedLine += bytes((u0Byte,));
        else:
          sb0IgnoredLine += bytes((u0Byte,));
        # Detect the prompt. This only works if the prompt starts on a new line!
        # The prompt normally contains pid and tid information, but for unknown reasons cdb can get confused about the
        # process it is debugging and show "?:???>"
        oPromptMatch = grbCdbPrompt.match(sbLine);
        if oPromptMatch:
          oCdbWrapper.sCdbCurrentISA = oPromptMatch.group(1) and "x86" or oCdbWrapper.sCdbISA;
          oCdbWrapper.fbFireCallbacks("Cdb stdout output", sbLine);
          if not bIgnoreOutput:
            assert not sb0StartOfCommandOutputMarker, \
                "No start of output marker found in command output:\r\n%s" % \
                "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbLines);
            # If there is an error during execution of the command, the end marker will not be output. In this case, see
            # if it is an expected and ignored error, or thrown an assertion:
            if sb0EndOfCommandOutputMarker:
              if not rb0IgnoredErrors or len(asbReturnedLines) == 0 or not rb0IgnoredErrors.match(asbReturnedLines[-1]):
                # The end-of-command marker is missing unexpectdly.
                raise cEndOfCommandOutputMarkerMissingException(asbReturnedLines);
          if oCdbWrapper.bGenerateReportHTML:
            # The prompt is always stored in a new block of I/O
            oCdbWrapper.sPromptHTML = "<span class=\"CDBPrompt\">%s</span>" % oCdbWrapper.fsHTMLEncode(sbLine);
          break;
  finally:
    if bApplicationWillBeRun:
      # Signal that the application is no longer running and wait for the interrupt on timeout thread to stop.
      oCdbWrapper.bApplicationIsRunning = False;
      oCdbWrapper.oInterruptOnTimeoutHelperThread.fWait();
  if bIgnoreOutput:
    return None;
  del asbLines;
  uIndex = 0;
  while uIndex < len(asbReturnedLines):
    sbLine = asbReturnedLines[uIndex];
    # The following error can be inserted by the symbol loader at any point in the output. It ends with a CRLF, so it
    # it will always run to the end of a line. The next line would have been a continuation of the current line, had
    # this error not been inserted.
    oSymbolLoadingError = re.search(grbSymbolLoadError, sbLine);
    if oSymbolLoadingError:
      # We can remove this error from the output by taking the line up to the start of the error and concatinating the
      # next line to reconstruct the intended output line without this error. The line is then processed again to
      # remove any further such errors, as there is no reason why a single line might not contain more than one such
      # error.
      sbLine = sbLine[:oSymbolLoadingError.start()];
      if uIndex + 1 < len(asRbeturnedLines):
        # There is more output after the error, which should be concatinated to the current line as the error
        # introduced the CRLF which broke the current line into two:
        sbLine += asbReturnedLines.pop(uIndex + 1);
        asbReturnedLines[uIndex] = sbLine;
      elif sbLine:
        # There is no more output after the error, just use the current line as-is.
        asbReturnedLines[uIndex] = sbLine;
      else:
        # There is no more output after the error and there was none before it; remove the line.
        asbReturnedLines.pop(uIndex);
      continue;
    uSkipLines = 0;
    # If a PDB file is corrupt, delete it so the next attempt to load it will download it again.
    oBadPDBFileError = grbBadPDBError.match(sbLine);
    if oBadPDBFileError:
      if dxConfig["bDeleteCorruptSymbols"] and oCdbWrapper.bUsingSymbolServers:
        sPDBFilePath = oBadPDBFileError.groups(1);
        # Try to delete the file.
        oPDBFile = cFileSystemItem(sPDBFilePath);
        assert oPDBFile.fbIsFile(), \
            "Cannot find PDB file %s from error %s" % (sPDBFilePath, repr(sbLine));
        assert oPDBFile.fbDelete(), \
            "Cannot delete PDB file %s from error %s" % (sPDBFilePath, repr(sbLine));
      asbReturnedLines.pop(uIndex);
      continue;
    oFailedToLoadSymbolsError = grbFailedToLoadSymbolsError.match(sbLine);
    if oFailedToLoadSymbolsError:
      if bHandleSymbolLoadErrors and oCdbWrapper.bUsingSymbolServers and dxConfig["uMaxSymbolLoadingRetries"] > 0:
        sbModuleFileName = [sb for sb in oFailedToLoadSymbolsError.groups() if s][0];
        # Try to reload the module symbols with noisy symbol loading on.
        oCdbWrapper.fasbExecuteCdbCommand(
          sbCommand = b"!sym noisy;.block {ld /f %s};!sym quiet;" % sbModuleFileName,
          sb0Comment = b"Attempt to noisily reload module symbols",
        );
      asbReturnedLines.pop(uIndex);
      continue;
    # This line should not be ignored, go to the next
    uIndex += 1;
  # Return the output
  return asbReturnedLines;
