from dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fApplicationStdOurOrErrThread(oCdbWrapper, uProcessId, oStdOurOrErrPipe, sStdOutOrErr):
  while 1:
    try:
      sLine = oStdOurOrErrPipe.fsReadLine();
    except IOError:
      break;
    if gbDebugIO: print "\r<app:%d/0x%X:%s<%s" % (uProcessId, uProcessId, sStdOutOrErr, sLine);
    if oCdbWrapper.bGenerateReportHTML:
      oCdbWrapper.sCdbIOHTML += "<span class=\"Application%s\">%s</span><br/>" % \
          (sStdOutOrErr, oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
    oCdbWrapper.fApplicationStdOurOrErrOutputCallback(uProcessId, sStdOutOrErr, sLine);
  
  if gbDebugIO: print "\r<app:%d/0x%X:%s:EOF" % (uProcessId, uProcessId, sStdOutOrErr);
