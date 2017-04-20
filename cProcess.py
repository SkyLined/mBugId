import os, re;
from cModule import cModule;

class cProcess(object):
  def __init__(oProcess, oCdbWrapper, uId, sBinaryName):
    oProcess.oCdbWrapper = oCdbWrapper;
    oProcess.uId = uId;
    oProcess.sBinaryName = sBinaryName;
    oProcess.__uPointerSize = None;
    oProcess.__uPageSize = None;
    oProcess.bNew = True; # Will be set to False by .fCdbStdInOutThread once application is run again.
    oProcess.bTerminated = False; # Will be set to True by .foSetCurrentProcessAfterApplicationRan once process is terminated
  
  @property
  def uPointerSize(oProcess):
    if oProcess.__uPointerSize is None:
      oProcess.__uPointerSize = oProcess.fuGetValue("@$ptrsize");
    return oProcess.__uPointerSize;
  
  @property
  def uPageSize(oProcess):
    if oProcess.__uPageSize is None:
      oProcess.__uPageSize = oProcess.fuGetValue("@$pagesize");
    return oProcess.__uPageSize;
  
  def fuGetValue(oProcess, sValueName):
    oCdbWrapper = oProcess.oCdbWrapper;
    oCdbWrapper.fSelectProcess(oProcess.uId);
    if not oCdbWrapper.bCdbRunning: return None;
    uValue = oCdbWrapper.fuGetValue(sValueName);
    if not oCdbWrapper.bCdbRunning: return None;
    return uValue;
  
  def __str__(oProcess):
    return 'Process(%s #%d)' % (oProcess.sBinaryName, oProcess.uProcessId);
  
  @classmethod
  def foCreateForCurrentProcess(cProcess, oCdbWrapper):
    # Gather process id and binary name for the current process.
    asProcessesInformationOutput = oCdbWrapper.fasSendCommandAndReadOutput("|.; $$ Get current process");
    if not oCdbWrapper.bCdbRunning: return None;
    #Output:
    # |.  2 id:  e44 child   name: chrome.exe
    # |.  1 id:  28c child   name: iexplore.exe
    # |.  4 id:  c74 exited  name: chrome.exe
    oProcessInformationMatch = len(asProcessesInformationOutput) == 1 and re.match(r"^\s*%s\s*$" % (
      r"\.\s+"                # "." whitespace
      r"\d+"                  # cdb_process_number
      r"\s+id:\s+"            # whitespace "id:" whitespace
      r"([0-9a-f]+)"          # (pid)
      r"\s+\w+\s+name:\s+"    # whitespace {"create" || "child"} whitespace "name:" whitespace
      r"(.*?)"                # (binary_name)
    ), asProcessesInformationOutput[0]);
    assert oProcessInformationMatch, \
        "Unexpected current process output:\r\n%s" % "\r\n".join(asProcessesInformationOutput);
    sProcessId, sBinaryNameOrPath = oProcessInformationMatch.groups();
    uProcessId = int(sProcessId, 16);
    if sBinaryNameOrPath == "?NoImage?":
      # No idea why this happens, but apparently it does...
      sBinaryName = None;
    else:
      sBinaryName = os.path.basename(sBinaryNameOrPath);
    return cProcess(oCdbWrapper, uProcessId, sBinaryName);
