import os, re;

from ..dxConfig import dxConfig;

def cProcess_fasbGetStack(oProcess, sbGetStackCommand):
  # Get the stack, which should make sure all relevant symbols are loaded or at least marked as requiring loading.
  # Noisy symbol loading is turned on during the command, so there will be symbol loading debug messages in between
  # the stack output, which makes the stack hard to parse: it is therefore discarded and the command is executed
  # again later (without noisy symbol loading) when symbols are loaded.
  # This only makes sense if we're using symbol servers, so we can download the symbols again if they fail.
  oProcess.fLoadSymbols();
  # Get the stack for real. At this point, no output from symbol loader is expected or handled.
  return oProcess.fasbExecuteCdbCommand(
    sbCommand = sbGetStackCommand,
    sb0Comment = b"Get stack",
    bOutputIsInformative = True,
  );
