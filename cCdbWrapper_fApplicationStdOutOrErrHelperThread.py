from .dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fApplicationStdOutOrErrHelperThread(oCdbWrapper, oConsoleProcess, oPipe, sPipeName):
  # sPipeName should be stdout or stderr
  uProcessId = oConsoleProcess.uId;
  while 1:
    try:
      sLine = oPipe.fsReadLine();
    except IOError:
      break;
    if gbDebugIO: print "\r<app:0x%X:%s<%s" % (oConsoleProcess.uId, sPipeName, sLine);
    oCdbWrapper.fbFireCallbacks("Application %s output" % sPipeName, oConsoleProcess, sLine);
    if oCdbWrapper.bGenerateReportHTML:
      sClassName = "Application%s" % {"stdout": "StdOut", "stderr": "StdErr"}[sPipeName];
      oCdbWrapper.sCdbIOHTML += "<span class=\"%s\">%s</span><br/>\n" % \
          (sClassName, oCdbWrapper.fsHTMLEncode(sLine, uTabStop = 8));
  if gbDebugIO: print "\r<app:0x%X:%s:EOF" % (oConsoleProcess.uId, sPipeName);
  oCdbWrapper.aoApplicationStdOutAndStdErrPipes.remove(oPipe);
  