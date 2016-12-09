import re, time;
from dxBugIdConfig import dxBugIdConfig;
from FileSystem import FileSystem;

dsTip_by_sErrorCode = {
  "Win32 error 0n2": "Did you provide the correct the path and name of the executable?",
  "NTSTATUS 0xC00000BB": "Are you using a 32-bit debugger with a 64-bit process?",
  "NTSTATUS 0xC000010A": "The process was terminated before the debugger could attach",
};

def fasHandleCommonErrorsAndWarningsInOutput(oCdbWrapper, asLines, bHandleSymbolLoadErrors):
  uIndex = 0;
  while uIndex < len(asLines):
    sLine = asLines[uIndex];
    # The following error can be inserted by the symbol loader at any point in the output. It ends with a CRLF, so it
    # it will always run to the end of a line. The next line would have been a continuation of the current line, had
    # this error not been inserted.
    oSymbolLoadingError = re.match(r"\*\*\* ERROR: Symbol file could not be found\.  Defaulted to export symbols for .* \- $", sLine);
    if oSymbolLoadingError:
      # We can remove this error from the output by taking the line up to the start of the error and concatinating the
      # next line to reconstruct the intended output line without this error. The line is then processed again to
      # remove any further such errors, as there is no reason why a single line might not contain more than one such
      # error.
      sLine = sLine[:oSymbolLoadingError.start()];
      if uIndex + 1 < len(asLines):
        # There is more output after the error, which should be concatinated to the current line as the error
        # introduced the CRLF which broke the current line into two:
        sLine += asLines.pop(uIndex + 1);
        asLines[uIndex] = sLine;
      elif sLine:
        # There is no more output after the error, just use the current line as-is.
        asLines[uIndex] = sLine;
      else:
        # There is no more output after the error and there was none before it; remove the line.
        asLines.pop(uIndex);
      continue;
    uSkipLines = 0;
    # Some of these errors can cause cdb to exit, so report them even if cdb is no longer running.
    oCannotAttachMatch = re.match(r"^Cannot (?:debug pid (\d+)|execute '(.*?)'), (Win32 error 0n\d+|NTSTATUS 0x\w+)\s*$", sLine);
    if oCannotAttachMatch: # Some of these errors can cause cdb to exit, so report them even if cdb is no longer running.
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
      return None;
    if oCdbWrapper.bCdbRunning:
      # These errors only need to be handled if cdb is still running.
      oBadPDBFileError = re.match(r"^%s\s*$" % "|".join([
        r"DBGHELP: (.*?) (\- E_PDB_CORRUPT|dia error 0x[0-9a-f]+)",
      ]), sLine);
      if oBadPDBFileError:
        sPDBFilePath = [s for s in oBadPDBFileError.groups() if s][0];
        # Try to delete the file. If this fails, wait a bit and retry. Repeat this a few times before giving up and
        # throwing an exception.
        FileSystem.fbDeleteFile(sPDBFilePath);
        uSkipLines = 1;
      else:
        oFailedToLoadSymbolsError = not oBadPDBFileError and bHandleSymbolLoadErrors and re.match(r"^%s\s*$" % "|".join([
          r"\*\*\* ERROR: Module load completed but symbols could not be loaded for (?:.*\\)*([^\\]+)",
        ]), sLine);
        if oFailedToLoadSymbolsError:
          if oCdbWrapper.bUsingSymbolServers: # We can try to download these again.
            sModuleFileName = [s for s in oFailedToLoadSymbolsError.groups() if s][0];
            # Turn noisy symbol loading on, reload the module and symbols, turn noisy symbol loading back off
            oCdbWrapper.fasSendCommandAndReadOutput(
              ".symopt+ 0x80000000;.reload /f /o /v /w %s;.symopt- 0x80000000; $$ Attempt to reload module symbols" %
                  sModuleFileName,
              bHandleSymbolLoadErrors = False,
            );
            if not oCdbWrapper.bCdbRunning: return;
          uSkipLines = 1;
        # Strip useless symbol warnings and errors:
        elif re.match(r"^%s\s*$" % "|".join([
          r"\*\*\* WARNING: Unable to verify checksum for .*",
          r"\*\*\* DBGHELP: SharedUserData \- virtual symbol module",
        ]), sLine):
          uSkipLines = 1;
      # This was some symbol loading error that should be removed from the output:
      for x in xrange(uSkipLines):
        asLines.pop(uIndex);
    if uSkipLines == 0:
      uIndex += 1;
  return asLines;

def cCdbWrapper_fasReadOutput(oCdbWrapper,
  bOutputIsInformative = False, \
  bOutputCanContainApplicationOutput = False,
  bHandleSymbolLoadErrors = True,
):
  sLine = "";
  asLines = [];
  bAddOutputToHTML = oCdbWrapper.bGenerateReportHTML and (
    dxBugIdConfig["bShowAllCdbCommandsInReport"]
    or (bOutputIsInformative and dxBugIdConfig["bShowInformativeCdbCommandsInReport"])
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
        if dxBugIdConfig["bOutputStdOut"]:
          print "cdb>%s" % repr(sLine)[1:-1];
        if re.match(r"^\(\w+\.\w+\): C\+\+ EH exception \- code \w+ \(first chance\)\s*$", sLine):
          # I cannot figure out how to detect second chance C++ exceptions without cdb outputting a line every time a
          # first chance C++ exception happens. These lines are clutter and MSIE outputs a lot of them, so they are
          # ignored here. TODO: find a way to break on second chance exceptions without getting a report about first
          # chance exceptions.
          pass; 
        else:
          if bAddOutputToHTML:
            sClass = bOutputCanContainApplicationOutput and "CDBOrApplicationStdOut" or "CDBStdOut";
            sLineHTML = "<span class=\"%s\">%s</span><br/>" % (sClass, oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
            # Add the line to the current block of I/O
            oCdbWrapper.asCdbStdIOBlocksHTML[-1] += sLineHTML;
            # Optionally add the line to the important output
            if bAddImportantLinesToHTML and oCdbWrapper.rImportantStdOutLines.match(sLine):
              oCdbWrapper.sImportantOutputHTML += sLineHTML;
          asLines.append(sLine);
      if sChar == "":
        break;
      sLine = "";
    else:
      sLine += sChar;
      # Detect the prompt. This only works if the prompt starts on a new line!
      oPromptMatch = re.match("^\d+:\d+(:x86)?> $", sLine);
      if oPromptMatch:
        if bAddOutputToHTML:
          nRunTime = time.clock() - nStartTime;
          oCdbWrapper.asCdbStdIOBlocksHTML[-1] += "(The above output was generated in %.1f seconds)<br/>" % nRunTime;
        oCdbWrapper.sCurrentISA = oPromptMatch.group(1) and "x86" or oCdbWrapper.sCdbISA;
        if dxBugIdConfig["bOutputStdOut"]:
          print "cdb>%s" % repr(sLine)[1:-1];
        if oCdbWrapper.bGenerateReportHTML:
          # The prompt is always stored in a new block of I/O
          oCdbWrapper.asCdbStdIOBlocksHTML.append("<span class=\"CDBPrompt\">%s</span>" % oCdbWrapper.fsHTMLEncode(sLine));
        return fasHandleCommonErrorsAndWarningsInOutput(oCdbWrapper, asLines, bHandleSymbolLoadErrors);
  oCdbWrapper.bCdbRunning = False;
  fasHandleCommonErrorsAndWarningsInOutput(oCdbWrapper, asLines, bHandleSymbolLoadErrors);
  return None;
