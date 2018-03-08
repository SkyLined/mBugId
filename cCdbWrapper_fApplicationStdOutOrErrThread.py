from .dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fApplicationStdOutOrErrThread(oCdbWrapper, oConsoleProcess, oStdOutOrErrPipe):
  uProcessId = oConsoleProcess.uId;
  sEventName = {
    "StdOut": "Application stdout output",
    "StdErr": "Application stderr output",
  }[oStdOutOrErrPipe.sDescription];
  while 1:
    try:
      sLine = oStdOutOrErrPipe.fsReadLine();
    except IOError:
      break;
    if gbDebugIO: print "\r<app:%d/0x%X:%s<%s" % (oConsoleProcess.uId, oConsoleProcess.uId, oStdOutOrErrPipe.sDescription, sLine);
    
    if oCdbWrapper.bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML += "<span class=\"Application%s\">%s</span><br/>\n" % \
          (oStdOutOrErrPipe.sDescription, oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
  if gbDebugIO: print "\r<app:%d/0x%X:%s:EOF" % (oConsoleProcess.uId, oConsoleProcess.uId, oStdOutOrErrPipe.sDescription);
    oCdbWrapper.fbFireEvent(sEventName, oConsoleProcess, sLine);
  