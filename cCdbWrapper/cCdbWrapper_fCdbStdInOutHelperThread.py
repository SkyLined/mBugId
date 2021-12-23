import re, time;

from mWindowsAPI import cJobObject;

from ..dxConfig import dxConfig;
from ..fnGetDebuggerTimeInSeconds import fnGetDebuggerTimeInSeconds;
from ..mCP437 import fsCP437FromBytesString;

grbDebuggerTime = re.compile(
  rb"^"
  rb"Debug session time: (.*?)"
  rb"\s*$"
);

def cCdbWrapper_fCdbStdInOutHelperThread(oCdbWrapper):
  # Create a job object to limit memory use if requested:
  if oCdbWrapper.u0ProcessMaxMemoryUse is not None or oCdbWrapper.u0TotalMaxMemoryUse is not None:
    oCdbWrapper.oJobObject = cJobObject();
    if oCdbWrapper.u0ProcessMaxMemoryUse is not None:
      oCdbWrapper.oJobObject.fSetMaxProcessMemoryUse(oCdbWrapper.u0ProcessMaxMemoryUse);
    if oCdbWrapper.u0TotalMaxMemoryUse is not None:
      oCdbWrapper.oJobObject.fSetMaxTotalMemoryUse(oCdbWrapper.u0TotalMaxMemoryUse);
  else:
    oCdbWrapper.oJobObject = None;
  # If we cannot apply memory limits, we'll fire an event. This should be done only once.
  oCdbWrapper.bFailedToApplyApplicationMemoryLimitsEventFired = True;
  # We may want to reserve some memory, which we'll track using this variable
  oReservedMemoryVirtualAllocation = None;
  # There are many exception that are handled by BugId and which should be hidden by the debugger from the application.
  # This boolean is set to True to indicate this, or False if the exception should be handled by application.
  bHideLastExceptionFromApplication = True; # The first exception is the initial breakpoint, which we hide
  # Create a list of commands to set up event handling.
  
  # Read the initial cdb output related to starting/attaching to the first process.
  oCdbWrapper.fasbReadOutput();
  # Turn off prompt information as it is not useful most of the time, but can clutter output and slow down
  # debugging by loading and resolving symbols.
  oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b".prompt_allow -dis -ea -reg -src -sym;",
    sb0Comment = b"Display only the prompt",
  );
  # Make sure the cdb prompt is on a new line after the application has been run:
  oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b'.pcmd -s ".printf \\"\\\\r\\\\n\\";";',
    sb0Comment = b"Output a CRLF after running the application",
  );
  oBugReport = None;
  uMainLoopCounter = 0;
  asbOutputWhileRunningApplication = [];
  oCdbWrapper.fAllocateReserveMemoryIfNeeded();
  while 1:
    uMainLoopCounter += 1;
    oCdbWrapper.fbFireCallbacks("Log message", "Main loop #%d" % uMainLoopCounter);
    (bEventIsFatal, bEventHasBeenHandled) = oCdbWrapper.ftbHandleLastCdbEvent(asbOutputWhileRunningApplication);
    if bEventIsFatal: # This indicates we need to stop.
      break;
    # (Re-)allocate reserve memory
    oCdbWrapper.fAllocateReserveMemoryIfNeeded();
    # bEventHasBeenHandled indicates the application should handle the event, not us.
    for (uProcessId, oProcess) in list(oCdbWrapper.doProcess_by_uId.items()):
      if oProcess.bTerminated:
        del oCdbWrapper.doProcess_by_uId[uProcessId];
    ### Attach to another process if needed ##########################################################################
    if oCdbWrapper.auProcessIdsPendingAttach:
      uProcessId = oCdbWrapper.auProcessIdsPendingAttach[0];
      oCdbWrapper.fAttachCdbToProcessForId(uProcessId);
    elif oCdbWrapper.o0UWPApplication and not oCdbWrapper.bUWPApplicationStarted:
    ### When debugging an UWP application, terminate any existing instances and start a new one. #####################
      if len(oCdbWrapper.asApplicationArguments) == 0:
        sbArgument = None;
      else:
        # This check should be superfluous, but it doesn't hurt to make sure.
        assert len(oCdbWrapper.asApplicationArguments) == 1, \
            "Expected exactly one argument";
        sbArgument = bytes(oCdbWrapper.asApplicationArguments[0], "ascii", "strict");
      oCdbWrapper.fTerminateUWPApplication(oCdbWrapper.o0UWPApplication);
      oCdbWrapper.fStartUWPApplication(oCdbWrapper.o0UWPApplication, sbArgument);
    else:
      # The application has been started.
      if len(oCdbWrapper.doProcess_by_uId) == 1:
        # There are no more application processes running.
        oCdbWrapper.fbFireCallbacks("Log message", "Application terminated");
        break;
      # We have attached to all processes; we're ready to debug the application.
      oCdbWrapper.fRunTimeoutCallbacks();
      ### Call application resumed callback before throwing away cached information ##################################
      oCdbWrapper.fbFireCallbacks("Application resumed");
    
    ### Clear cache ##################################################################################################
    oCdbWrapper.oCdbCurrentProcess = None;
    oCdbWrapper.oCdbCurrentWindowsAPIThread = None;
    for (uProcessId, oProcess) in oCdbWrapper.doProcess_by_uId.items():
      oProcess.fClearCache();
    
    ### Keep track of time #########################################################################################
    # Mark the time when the application was resumed.
    asbCdbTimeOutput = oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = b".time;",
      sb0Comment = b"Get debugger time",
      bRetryOnTruncatedOutput = True,
    );
    oTimeMatch = len(asbCdbTimeOutput) > 0 and grbDebuggerTime.match(asbCdbTimeOutput[0]);
    assert oTimeMatch, \
        "Failed to get debugger time!\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCdbTimeOutput);
    del asbCdbTimeOutput;
    oCdbWrapper.oApplicationTimeLock.fAcquire();
    try:
      oCdbWrapper.nApplicationResumeDebuggerTimeInSeconds = fnGetDebuggerTimeInSeconds(oTimeMatch.group(1));
      oCdbWrapper.nApplicationResumeTimeInSeconds = time.time();
    finally:
      oCdbWrapper.oApplicationTimeLock.fRelease();
    ### Resume application ###########################################################################################
    if oCdbWrapper.bStopping: break; # Unless we have been requested to stop.
    asbOutputWhileRunningApplication = oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = b"g%s;" % (bEventHasBeenHandled and b"h" or b"n"), # If the event has not been handled, pass it to the application.
      sb0Comment = b"Running application",
      bOutputIsInformative = True,
      bApplicationWillBeRun = True, # This command will cause the application to run.
      bUseMarkers = False, # This does not work with g commands: the end marker will never be shown.
    );
    ### The debugger suspended the application #######################################################################
    # Send a nop command to cdb in case the application being debugged is reading stdin as well: in that case it may
    # eat the first char we try to send to cdb, which would otherwise cause a problem when cdb see only the part of
    # the command after the first char.
    oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = b" ",
      sb0Comment = None,
      bIgnoreOutput = True,
      bUseMarkers = False,
    );
  
  # Terminate cdb.
  oCdbWrapper.fbFireCallbacks("Log message", "Terminating cdb.exe");
  oCdbWrapper.bCdbWasTerminatedOnPurpose = True;
  oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b"q",
    sb0Comment = b"Terminate cdb",
    bIgnoreOutput = True,
    bUseMarkers = False
  );
  # The above should raise a cCdbTerminedException, so the below should not be reached.
  raise AssertionError("Cdb failed to terminate after sending 'q' command");
