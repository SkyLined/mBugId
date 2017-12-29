from dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fApplicationStdOutOrErrThread(oCdbWrapper, oConsoleProcess, oStdOutOrErrPipe):
  uProcessId = oConsoleProcess.uId;
  while 1:
    try:
      sLine = oStdOutOrErrPipe.fsReadLine();
    except IOError:
      break;
    if gbDebugIO: print "\r<app:%d/0x%X:%s<%s" % (oConsoleProcess.uId, oConsoleProcess.uId, oStdOutOrErrPipe.sDescription, sLine);
    sEventName = {
      "StdOut": "Application stdout output",
      "StdErr": "Application stderr output",
    }[oStdOutOrErrPipe.sDescription];
    
    if oCdbWrapper.bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML += "<span class=\"Application%s\">%s</span><br/>" % \
          (oStdOutOrErrPipe.sDescription, oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
    oCdbWrapper.fbFireEvent(
      sEventName,
      oConsoleProcess.uId,
      oConsoleProcess.oInformation.sBinaryName,
      oConsoleProcess.oInformation.sCommandLine,
      sLine
    );
  if gbDebugIO: print "\r<app:%d/0x%X:%s:EOF" % (oConsoleProcess.uId, oConsoleProcess.uId, oStdOutOrErrPipe.sDescription);
