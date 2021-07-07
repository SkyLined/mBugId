from .fsbExceptionHandlingCdbCommands import fsbExceptionHandlingCdbCommands;

def cCdbWrapper_fHandleAttachedToUtilityProcess(oCdbWrapper):
  # This is the utility process; cdb has loaded and started it. Go set some things up.
  # Set up exception handling and record the utility process' id.
  oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = fsbExceptionHandlingCdbCommands(),
    sb0Comment = b"Setup exception handling",
  );
  oCdbWrapper.fbFireCallbacks("Log message", "Attached to utility process", {
    "Process id": "%d/0x%X" % (oCdbWrapper.oUtilityProcess.uId, oCdbWrapper.oUtilityProcess.uId),
  });
