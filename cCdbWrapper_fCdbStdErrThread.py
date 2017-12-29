from dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fCdbStdErrThread(oCdbWrapper):
  sLine = "";
  while 1:
    try:
      sLine = oCdbWrapper.oCdbConsoleProcess.oStdErrPipe.fsReadLine();
    except IOError:
      if gbDebugIO: print "\r<stderr:EOF<";
      break;
    if gbDebugIO: print "\r<stderr<%s" % sLine;
    oCdbWrapper.asStdErrOutput.append(sLine);
    if oCdbWrapper.bGenerateReportHTML:
      sLineHTML = "<span class=\"CDBStdErr\">%s</span><br/>" % oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8);
      oCdbWrapper.sCdbIOHTML += sLineHTML;
      oCdbWrapper.fbFireEvent("Log message", "StdErr output", {
        "Line": sLine,
      });
    oCdbWrapper.fbFireEvent("Cdb stderr output", sLine);
  oCdbWrapper.bCdbRunning = False;

