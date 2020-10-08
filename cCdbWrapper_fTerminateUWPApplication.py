def cCdbWrapper_fTerminateUWPApplication(oCdbWrapper, oUWPApplication):
  oCdbWrapper.fbFireCallbacks("Log message", "Terminating UWP application", {
    "Application Id": oUWPApplication.sApplicationId, 
    "Package name": oUWPApplication.sPackageName, 
    "Package full name": oUWPApplication.sPackageFullName, 
  });
  # Kill it so we are sure to run a fresh copy.
  asTerminateUWPApplicationOutput = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".terminatepackageapp %s;" % oUWPApplication.sPackageFullName,
    sComment = "Terminate UWP application %s" % oUWPApplication.sPackageName,
  );
  if asTerminateUWPApplicationOutput == [
    "Failed - error: HRESULT 0x80010108",
    "    \"The object invoked has disconnected from its clients.\"",
  ]:
    # This suggest that the command was not executed successfully because an RPC channel broke. I'm trying to find out
    # if this can be solved by executing the command again (assuming a new RPC channel will get set up and this second
    # call will succeed). In order to find out, I will throw an assertion error either way and have the error message
    # report whether retrying is useful or not. If it is, this code should probably be in a loop that retries N times
    # until success, or reports an error if it still fails after that many tries.
    asTerminateUWPApplicationOutput2 = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = ".terminatepackageapp %s;" % oUWPApplication.sPackageFullName,
      sComment = "Terminate UWP application %s" % oUWPApplication.sPackageName,
    );
    assert asTerminateUWPApplicationOutput == asTerminateUWPApplicationOutput2, \
        "Repeating the .terminatepackageapp command does not appear to be useful";
    assert False, \
        "Repeating the .terminatepackageapp command resulted in:\r\n%s" % "\r\n".join(asTerminateUWPApplicationOutput2);
  if asTerminateUWPApplicationOutput:
    assert asTerminateUWPApplicationOutput == ['The "terminatePackageApp" action will be completed on next execution.'], \
        "Unexpected .terminatepackageapp output:\r\n%s" % "\r\n".join(asTerminateUWPApplicationOutput);

