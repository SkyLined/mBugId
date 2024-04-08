from ..mCP437 import fsCP437HTMLFromString;

gbDebugIO = False; # Used for debugging cdb I/O issues

def cCdbWrapper_fCdbStdErrHelperThread(oCdbWrapper):
  sLine = "";
  while 1:
    s0Line = oCdbWrapper.oCdbConsoleProcess.oStdErrPipe.fs0ReadLine();
    if s0Line is None:
      if gbDebugIO: print("\r<stderr:EOF<");
      oCdbWrapper.fbFireCallbacks("Log message", "Failed to read from cdb.exe stderr");
      break;
    if gbDebugIO: print("\r<stderr<%s" % s0Line);
    if oCdbWrapper.bGenerateReportHTML:
      sLineHTML = "<span class=\"CDBStdErr\">%s</span><br/>\n" % fsCP437HTMLFromString(s0Line, u0TabStop = 8);
      oCdbWrapper.sCdbIOHTML += sLineHTML;
    oCdbWrapper.fbFireCallbacks("Log message", "StdErr output", {
      "Line": s0Line,
    });
    oCdbWrapper.fbFireCallbacks("Cdb stderr output", s0Line);
  oCdbWrapper.bCdbIsRunning = False;
