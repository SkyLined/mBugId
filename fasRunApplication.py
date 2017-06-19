import subprocess;

def fasRunApplication(*asCommandLine):
  sCommandLine = " ".join([" " in s and '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"') or s for s in asCommandLine]);
  oProcess = subprocess.Popen(
    args = sCommandLine,
    stdin = subprocess.PIPE,
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE,
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP,
  );
  (sStdOut, sStdError) = oProcess.communicate();
  assert not sStdError, \
      "Error running %s:\r\n%s" % (sCommandLine, sStdErr);
  asStdOut = sStdOut.split("\r\n");
  if asStdOut[-1] == "":
    asStdOut.pop();
  return asStdOut;
