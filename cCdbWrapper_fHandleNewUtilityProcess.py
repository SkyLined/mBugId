from .fsExceptionHandlingCdbCommands import fsExceptionHandlingCdbCommands;

def cCdbWrapper_fHandleNewUtilityProcess(oCdbWrapper, uProcessId):
  # This is the utility process; cdb has loaded and started it. Go set some things up.
  # Set up exception handling and record the utility process' id.
  oCdbWrapper.uUtilityProcessId = uProcessId;
  oCdbWrapper.fasExecuteCdbCommand(
    sCommand = fsExceptionHandlingCdbCommands(),
    sComment = "Setup exception handling",
  );
  oCdbWrapper.fbFireEvent("Log message", "Utility process created", {
    "Process id": "%d/0x%X" % (uProcessId, uProcessId),
  });
