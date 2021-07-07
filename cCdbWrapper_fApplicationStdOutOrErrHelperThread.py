from .dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fApplicationStdOutOrErrHelperThread(oCdbWrapper, oConsoleProcess, oPipe, sPipeName):
  # sPipeName should be stdout or stderr
  uProcessId = oConsoleProcess.uId;
  while 1:
    s0Line = oPipe.fs0ReadLine();
    if s0Line is None:
      break;
    if gbDebugIO: print("\r<app:0x%X:%s<%s" % (oConsoleProcess.uId, sPipeName, s0Line));
    oCdbWrapper.fbFireCallbacks("Application %s output" % sPipeName, oConsoleProcess, s0Line);
    if oCdbWrapper.bGenerateReportHTML:
      sClassName = "Application%s" % {"stdout": "StdOut", "stderr": "StdErr"}[sPipeName];
      oCdbWrapper.sCdbIOHTML += "<span class=\"%s\">%s</span><br/>\n" % \
          (sClassName, oCdbWrapper.fsHTMLEncode(s0Line, uTabStop = 8));
  if gbDebugIO: print("\r<app:0x%X:%s:EOF" % (oConsoleProcess.uId, sPipeName));
  oCdbWrapper.aoApplicationStdOutAndStdErrPipes.remove(oPipe);
  