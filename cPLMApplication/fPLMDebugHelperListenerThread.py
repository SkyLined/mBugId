import re;
from fNamedPipeDataReceivingServer import fNamedPipeDataReceivingServer;

from ..dxConfig import dxConfig;

def fPLMDebugHelperListenerThread(oCdbWrapper):
  # This thread listens for PLM Debug helper messages using a named thread, and parses them:
  def fbHandleData(sData):
    # Check if we have been asked to terminate.
    if sData == "*END*":
      return False;
    # Check that the message contains a process and thread id.
    oProcessAndThreadIdMatch = re.match(r"\-p (\d+) \-tid (\d+)", sData);
    assert oProcessAndThreadIdMatch, \
        "Got unrecognized message over %s named pipe: %s" % (repr(dxConfig["sPLMDebugHelperPipeName"]), repr(sData));
    sProcessId, sThreadId = oProcessAndThreadIdMatch.groups();
    # Give the process id to the callback handler
    oCdbWrapper.fAttachToProcessById(long(sProcessId));
    return True;
  
  fNamedPipeDataReceivingServer(dxConfig["sPLMDebugHelperPipeName"], fbHandleData);
