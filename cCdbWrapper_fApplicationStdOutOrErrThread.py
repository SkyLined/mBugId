from dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fApplicationStdOutOrErrThread( \
    oCdbWrapper, uProcessId, sBinaryName, sCommandLine, oStdOutOrErrPipe, sStdOutOrErr,
  ):
  while 1:
    try:
      sLine = oStdOutOrErrPipe.fsReadLine();
    except IOError:
      break;
    if gbDebugIO: print "\r<app:%d/0x%X:%s<%s" % (uProcessId, uProcessId, sStdOutOrErr, sLine);
    if oCdbWrapper.bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML += "<span class=\"Application%s\">%s</span><br/>" % \
          (sStdOutOrErr, oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
    sEventName = {
      "StdOut": "Application stdout output",
      "StdErr": "Application stderr output",
    }[sStdOutOrErr];
    oCdbWrapper.fbFireEvent(sEventName, uProcessId, sBinaryName, sCommandLine, sLine);
  if gbDebugIO: print "\r<app:%d/0x%X:%s:EOF" % (uProcessId, uProcessId, sStdOutOrErr);
