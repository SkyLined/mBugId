from .dxConfig import dxConfig;

gbDebugIO = False; # Used for debugging cdb I/O issues
from .cBugReport_UnhandledPythonException import cBugReport_UnhandledPythonException;

def cCdbWrapper_fCdbStdErrHelperThread(oCdbWrapper):
  try:
    sLine = "";
    while 1:
      s0Line = oCdbWrapper.oCdbConsoleProcess.oStdErrPipe.fs0ReadLine();
      if s0Line is None:
        if gbDebugIO: print("\r<stderr:EOF<");
        oCdbWrapper.fbFireCallbacks("Log message", "Failed to read from cdb.exe stderr");
        break;
      if gbDebugIO: print("\r<stderr<%s" % s0Line);
      if oCdbWrapper.bGenerateReportHTML:
        sLineHTML = "<span class=\"CDBStdErr\">%s</span><br/>\n" % oCdbWrapper.fsHTMLEncode(s0Line, uTabStop = 8);
        oCdbWrapper.sCdbIOHTML += sLineHTML;
      oCdbWrapper.fbFireCallbacks("Log message", "StdErr output", {
        "Line": s0Line,
      });
      oCdbWrapper.fbFireCallbacks("Cdb stderr output", s0Line);
    oCdbWrapper.bCdbIsRunning = False;
  except Exception as oException:
    oBugReport = cBugReport_UnhandledPythonException(oCdbWrapper, oException);
    oBugReport.fReport();

