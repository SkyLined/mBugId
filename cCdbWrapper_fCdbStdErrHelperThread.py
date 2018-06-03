from .dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fCdbStdErrHelperThread(oCdbWrapper):
  sLine = "";
  while 1:
    try:
      sLine = oCdbWrapper.oCdbConsoleProcess.oStdErrPipe.fsReadLine();
    except IOError:
      if gbDebugIO: print "\r<stderr:EOF<";
      oCdbWrapper.fbFireEvent("Log message", "Failed to read from cdb.exe stderr");
      break;
    if gbDebugIO: print "\r<stderr<%s" % sLine;
    if oCdbWrapper.bGenerateReportHTML:
      sLineHTML = "<span class=\"CDBStdErr\">%s</span><br/>\n" % oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8);
      oCdbWrapper.sCdbIOHTML += sLineHTML;
    oCdbWrapper.fbFireEvent("Log message", "StdErr output", {
      "Line": sLine,
    });
    oCdbWrapper.fbFireEvent("Cdb stderr output", sLine);
  oCdbWrapper.bCdbRunning = False;

