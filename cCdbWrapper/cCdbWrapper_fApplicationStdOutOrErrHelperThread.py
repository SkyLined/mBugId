from ..mCP437 import fsCP437HTMLFromString;

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
          (sClassName, fsCP437HTMLFromString(s0Line, u0TabStop = 8));
  if gbDebugIO: print("\r<app:0x%X:%s:EOF" % (oConsoleProcess.uId, sPipeName));
  oCdbWrapper.oApplicationStdOutAndStdErrPipeLock.fAcquire();
  try:
    aoApplicationStdOutAndStdErrPipes = oCdbWrapper.daoApplicationStdOutAndStdErrPipes_by_uProcessId[uProcessId];
    aoApplicationStdOutAndStdErrPipes.remove(oPipe);
    if len(aoApplicationStdOutAndStdErrPipes) == 0:
      del oCdbWrapper.daoApplicationStdOutAndStdErrPipes_by_uProcessId[uProcessId];
  finally:
    oCdbWrapper.oApplicationStdOutAndStdErrPipeLock.fRelease();
