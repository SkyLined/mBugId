import re;

def cCdbWrapper_fAttachToProcessesForBinaryNames(oCdbWrapper, asBinaryNames):
  # binary names are case-insensitive, make list lower case for easier comparison:
  asBinaryNames = [s.lower() for s in asBinaryNames];
  # List all processes and their binary names:
  asRunningProcessesOutput = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".tlist;",
    sComment = "list running processes",
  );
  for sLine in asRunningProcessesOutput:
    # Parse each line
    oProcessMatch = re.match("^\s*0n(\d+) (.*)$", sLine);
    assert oProcessMatch, \
        "Unexpected .tlist output %s:\r\n%s" % (repr(sLine), "\r\n".join(asRunningProcessesOutput));
    sProcessId, sProcessBinaryName = oProcessMatch.groups();
    # Check if this process is running on of the requested binaries
    if sProcessBinaryName.lower() in asBinaryNames:
      uProcessId = long(sProcessId);
      # If it is not yet being debugged, do so:
      if uProcessId not in oCdbWrapper.doProcess_by_uId and uProcessId not in oCdbWrapper.auProcessIdsPendingAttach:
        oCdbWrapper.auProcessIdsPendingAttach.append(uProcessId);
