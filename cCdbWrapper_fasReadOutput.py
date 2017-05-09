import re, time;
from cCdbStoppedException import cCdbStoppedException;
from dxConfig import dxConfig;
from FileSystem import FileSystem;

dsTip_by_sErrorCode = {
  "Win32 error 0n2": "Did you provide the correct the path and name of the executable?",
  "NTSTATUS 0xC00000BB": "Are you using a 32-bit debugger with a 64-bit process?",
  "NTSTATUS 0xC000010A": "The process was terminated before the debugger could attach",
};

rAlwaysIgnoredLines = re.compile("^(%s)$" % "|".join([
  r"\*\*\* ERROR: Symbol file could not be found.  Defaulted to export symbols for .*",
  r"\*\*\* WARNING: Unable to verify checksum for .*",
]));

def cCdbWrapper_fasReadOutput(oCdbWrapper,
  bOutputIsInformative = False,
  bOutputCanContainApplicationOutput = False,
  bHandleSymbolLoadErrors = True,
  bIgnoreOutput = False,
  srIgnoreErrors = None,
  sStartOfCommandOutputMarker = None, # Every command is preceded and followed by commands that outputs marker strings.
  sEndOfCommandOutputMarker = None,   # These are used to detect where the output of the cdb command starts in cases
                                      # where the application has output something out of sync. The applications output
                                      # should either precede or follow the command output markers. This allowing us
                                      # to ignore the application output and only return the command output to the
                                      # caller.
):
  sLine = "";
  if not bIgnoreOutput:
    asLines = [];
    asReturnedLines = [];
    if sStartOfCommandOutputMarker:
      assert sEndOfCommandOutputMarker, "duh";
      sReturnedLine = None;
      sIgnoredLine = "";
    else:
      assert sEndOfCommandOutputMarker is None, "duh";
      sReturnedLine = "";
      sIgnoredLine = None;
    bAddOutputToHTML = oCdbWrapper.bGenerateReportHTML and (
      dxConfig["bShowAllCdbCommandsInReport"]
      or (bOutputIsInformative and dxConfig["bShowInformativeCdbCommandsInReport"])
      or bOutputCanContainApplicationOutput
    );
    bAddImportantLinesToHTML = oCdbWrapper.bGenerateReportHTML and (
      bOutputCanContainApplicationOutput
      and oCdbWrapper.rImportantStdOutLines
    );
    if bAddOutputToHTML:
      nStartTime = time.clock();
  while 1:
    sChar = oCdbWrapper.oCdbProcess.stdout.read(1);
    if sChar == "\r":
      pass; # ignored.
    elif sChar in ("\n", ""):
      if sChar == "\n" or sLine:
        if dxConfig["bOutputStdOut"]:
          print "cdb>%s" % repr(sLine)[1:-1];
        # Failure to attach will terminate cdb. This needs to be special cased:
        oCannotAttachMatch = re.match(r"^Cannot (?:debug pid (\d+)|execute '(.*?)'), (Win32 error 0n\d+|NTSTATUS 0x\w+)\s*$", sLine);
        if oCannotAttachMatch:
          sProcessId, sApplicationExecutable, sErrorCode = oCannotAttachMatch.groups();
          if sProcessId:
            uProcessId = long(sProcessId);
            sErrorMessage = "Failed to attach to process %d/0x%X: %s!" % (uProcessId, uProcessId, sErrorCode);
          else:
            sErrorMessage = "Failed to start application \"%s\": %s!" % (sApplicationExecutable, sErrorCode);
          if sErrorCode in dsTip_by_sErrorCode:
            sErrorMessage += "\r\n" + dsTip_by_sErrorCode[sErrorCode];
          oCdbWrapper.fFailedToDebugApplicationCallback(sErrorMessage);
          oCdbWrapper.fStop();
        if re.match(r"^\(\w+\.\w+\): C\+\+ EH exception \- code \w+ \(first chance\)\s*$", sLine):
          # I cannot figure out how to detect second chance C++ exceptions without cdb outputting a line every time a
          # first chance C++ exception happens. These lines are clutter and MSIE outputs a lot of them, so they are
          # ignored here. TODO: find a way to break on second chance exceptions without getting a report about first
          # chance exceptions.
          pass; 
        elif not bIgnoreOutput:
          if bAddOutputToHTML and oCdbWrapper.asCdbStdIOBlocksHTML is not None:
            while 1:
              try:
                sClass = bOutputCanContainApplicationOutput and "CDBOrApplicationStdOut" or "CDBStdOut";
                sLineHTML = "<span class=\"%s\">%s</span><br/>" % (sClass, oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
                # Add the line to the current block of I/O
                oCdbWrapper.asCdbStdIOBlocksHTML[-1] += sLineHTML;
                # Optionally add the line to the important output
                if bAddImportantLinesToHTML and oCdbWrapper.rImportantStdOutLines.match(sLine):
                  oCdbWrapper.sImportantOutputHTML += sLineHTML;
                break;
              except MemoryError:
                if len(oCdbWrapper.asCdbStdIOBlocksHTML) < 2: raise;
                oCdbWrapper.asCdbStdIOBlocksHTML[0] = "(First lines removed because BugId ran out of memory)";
                oCdbWrapper.asCdbStdIOBlocksHTML.pop(1);
          asLines.append(sLine);
          # Strip useless symbol warnings and errors:
          if sIgnoredLine is not None:
            bStartOfCommandOutput = sStartOfCommandOutputMarker and sIgnoredLine.endswith(sStartOfCommandOutputMarker);
            if bStartOfCommandOutput:
              sIgnoredLine = sIgnoredLine[:-len(sStartOfCommandOutputMarker)]; # Remove the marker from the line;
            if sIgnoredLine:
              if sIgnoredLine == sLine:
                print "IGNORED %s" % repr(sIgnoredLine);
              else:
                print "IGNORED %s in %s" % (repr(sIgnoredLine), repr(sLine));
            if bStartOfCommandOutput:
              sReturnedLine = ""; # Start collecting lines to return to the caller.
              sIgnoredLine = None; # Stop ignoring lines
              sStartOfCommandOutputMarker = None; # Stop looking for the marker.
          else:
            bEndOfCommandOutput = sEndOfCommandOutputMarker and sReturnedLine.endswith(sEndOfCommandOutputMarker);
            if bEndOfCommandOutput:
              sReturnedLine = sReturnedLine[:-len(sEndOfCommandOutputMarker)]; # Remove the marker from the line;
            if sReturnedLine:
              if rAlwaysIgnoredLines.match(sReturnedLine):
                if sReturnedLine == sLine:
                  print "IGNORED %s" % repr(sReturnedLine);
                elif sIgnoredLine:
                  print "IGNORED %s in %s" % (repr(sReturnedLine), repr(sLine));
              else:
                asReturnedLines.append(sReturnedLine);
            if bEndOfCommandOutput:
              sEndOfCommandOutputMarker = None; # Stop looking for the marker.
              sReturnedLine = None; # Stop collecting lines to return to the caller.
              sIgnoredLine = ""; # Start ignoring lines
      if sChar == "":
        oCdbWrapper.bCdbRunning = False;
        raise cCdbStoppedException();
      sLine = "";
      if not bIgnoreOutput:
        if sReturnedLine is not None:
          sReturnedLine = "";
        else:
          sIgnoredLine = "";
    else:
      sLine += sChar;
      if not bIgnoreOutput:
        if sReturnedLine is not None:
          sReturnedLine += sChar;
        else:
          sIgnoredLine += sChar;
      # Detect the prompt. This only works if the prompt starts on a new line!
      oPromptMatch = re.match("^\d+:\d+(:x86)?> $", sLine);
      if oPromptMatch:
        oCdbWrapper.sCurrentISA = oPromptMatch.group(1) and "x86" or oCdbWrapper.sCdbISA;
        if dxConfig["bOutputStdOut"]:
          print "cdb>%s" % repr(sLine)[1:-1];
        if not bIgnoreOutput:
          assert not sStartOfCommandOutputMarker, \
              "No start of output marker found in command output:\r\n%s" % "\r\n".join(asLines);
          # If there is an error during execution of the command, the end marker will not be output. In this case, see
          # if it is an expected and ignored error, or thrown an assertion:
          assert not sEndOfCommandOutputMarker or (srIgnoreErrors and len(asReturnedLines) == 1 and re.match(srIgnoreErrors, asReturnedLines[0])), \
              "The command output appears to report an error:\r\n%s" % "\r\n".join([repr(sLine) for sLine in asReturnedLines]);
          if bAddOutputToHTML:
            nRunTime = time.clock() - nStartTime;
            oCdbWrapper.asCdbStdIOBlocksHTML[-1] += "(The above output was generated in %.1f seconds)<br/>" % nRunTime;
          if oCdbWrapper.bGenerateReportHTML:
            # The prompt is always stored in a new block of I/O
            oCdbWrapper.asCdbStdIOBlocksHTML.append("<span class=\"CDBPrompt\">%s</span>" % oCdbWrapper.fsHTMLEncode(sLine));
        break;
  if bIgnoreOutput:
    return;
  uIndex = 0;
  while uIndex < len(asReturnedLines):
    sLine = asReturnedLines[uIndex];
    # The following error can be inserted by the symbol loader at any point in the output. It ends with a CRLF, so it
    # it will always run to the end of a line. The next line would have been a continuation of the current line, had
    # this error not been inserted.
    oSymbolLoadingError = re.search(r"\*\*\* ERROR: Symbol file could not be found\.  Defaulted to export symbols for .*$", sLine);
    if oSymbolLoadingError:
      # We can remove this error from the output by taking the line up to the start of the error and concatinating the
      # next line to reconstruct the intended output line without this error. The line is then processed again to
      # remove any further such errors, as there is no reason why a single line might not contain more than one such
      # error.
      sLine = sLine[:oSymbolLoadingError.start()];
      if uIndex + 1 < len(asReturnedLines):
        # There is more output after the error, which should be concatinated to the current line as the error
        # introduced the CRLF which broke the current line into two:
        sLine += asReturnedLines.pop(uIndex + 1);
        asReturnedLines[uIndex] = sLine;
      elif sLine:
        # There is no more output after the error, just use the current line as-is.
        asReturnedLines[uIndex] = sLine;
      else:
        # There is no more output after the error and there was none before it; remove the line.
        asReturnedLines.pop(uIndex);
      continue;
    uSkipLines = 0;
    # If a PDB file is corrupt, delete it so the next attempt to load it will download it again.
    oBadPDBFileError = re.match(r"^DBGHELP: (.+) (?:\- E_PDB_CORRUPT|dia error 0x[0-9a-f]+)\s*$", sLine);
    if oBadPDBFileError:
      if dxConfig["bDeleteCorruptSymbols"] and oCdbWrapper.bUsingSymbolServers:
        sPDBFilePath = oBadPDBFileError.groups(1);
        # Try to delete the file. If this fails, wait a bit and retry. Repeat this a few times before giving up and
        # throwing an exception.
        FileSystem.fbDeleteFile(sPDBFilePath);
      asReturnedLines.pop(uIndex);
      continue;
    oFailedToLoadSymbolsError = re.match(r"^\*\*\* ERROR: Module load completed but symbols could not be loaded for (?:.*\\)*([^\\]+)", sLine);
    if oFailedToLoadSymbolsError:
      if bHandleSymbolLoadErrors and oCdbWrapper.bUsingSymbolServers and dxConfig["uMaxSymbolLoadingRetries"] > 0:
        sModuleFileName = [s for s in oFailedToLoadSymbolsError.groups() if s][0];
        # Try to reload the module symbols with noisy symbol loading on.
        oCdbWrapper.fasSendCommandAndReadOutput("!sym noisy;");
        oCdbWrapper.fasSendCommandAndReadOutput("ld /f %s;$$ Attempt to reload symbols" % sModuleFileName,
          bHandleSymbolLoadErrors = False, # Let's no trigger an infinite loop
        );
        oCdbWrapper.fasSendCommandAndReadOutput("!sym quiet");
      asReturnedLines.pop(uIndex);
      continue;
    # This line should not be ignored, go to the next
    uIndex += 1;
  # Return the output
  return asReturnedLines;
