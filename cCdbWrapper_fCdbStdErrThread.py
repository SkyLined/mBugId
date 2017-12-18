from dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fCdbStdErrThread(oCdbWrapper):
  sLine = "";
  while 1:
    try:
      sChar = oCdbWrapper.oCdbProcess.stderr.read(1);
    except IOError:
      sChar = "";
    if sChar == "\r":
      pass; # ignored.
    elif sChar in ("\n", ""):
      if gbDebugIO: print "\r<stderr<%s" % sLine;
      if sChar == "\n" or sLine:
        oCdbWrapper.asStdErrOutput.append(sLine);
        if oCdbWrapper.bGenerateReportHTML:
          sLineHTML = "<span class=\"CDBStdErr\">%s</span><br/>" % oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8);
          oCdbWrapper.sCdbIOHTML += sLineHTML;
          bImportant = oCdbWrapper.rImportantStdErrLines and oCdbWrapper.rImportantStdErrLines.match(sLine);
          oCdbWrapper.fLogMessageInReport(
            bImportant and "LogImportantStdErrOutput" or "LogStdErrOutput",
            sLine
          );
        oCdbWrapper.fbFireEvent("Cdb stderr output", sLine);
      if sChar == "":
        if gbDebugIO: print "\r<stderr:EOF<";
        break;
      sLine = "";
    else:
      if gbDebugIO: print "\r<stderr<%s" % sLine,;
      sLine += sChar;
  oCdbWrapper.bCdbRunning = False;

