def cCdbWrapper_fTerminateUWPApplication(oCdbWrapper, oUWPApplication):
  oCdbWrapper.fbFireCallbacks("Log message", "Terminating UWP application", {
    "Application Id": oUWPApplication.sApplicationId, 
    "Package name": oUWPApplication.sPackageName, 
    "Package full name": oUWPApplication.sPackageFullName, 
  });
  # Kill it so we are sure to run a fresh copy.
  sbPackageName = bytes(oUWPApplication.sPackageName, 'latin1');
  sbPackageFullName = bytes(oUWPApplication.sPackageFullName, 'latin1');
  asbTerminateUWPApplicationOutput = oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b".terminatepackageapp %s;" % sbPackageFullName,
    sb0Comment = b"Terminate UWP application %s" % sbPackageName,
  );
  if asbTerminateUWPApplicationOutput == [
    b"Failed - error: HRESULT 0x80010108",
    b"    \"The object invoked has disconnected from its clients.\"",
  ]:
    # This suggest that the command was not executed successfully because an RPC channel broke. I'm trying to find out
    # if this can be solved by executing the command again (assuming a new RPC channel will get set up and this second
    # call will succeed). In order to find out, I will throw an assertion error either way and have the error message
    # report whether retrying is useful or not. If it is, this code should probably be in a loop that retries N times
    # until success, or reports an error if it still fails after that many tries.
    asbTerminateUWPApplicationOutput2 = oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = b".terminatepackageapp %s;" % sbPackageFullName,
      sb0Comment = b"Terminate UWP application %s" % sbPackageName,
    );
    assert asbTerminateUWPApplicationOutput == asbTerminateUWPApplicationOutput2, \
        "Cannot terminate UWP App and repeating the .terminatepackageapp command does not appear to be useful: %s" % \
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbTerminateUWPApplicationOutput2);
    assert False, \
        "Cannot terminate UWP App and repeating the .terminatepackageapp command gives an unknown error: %s" % \
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbTerminateUWPApplicationOutput2);
  if asbTerminateUWPApplicationOutput:
    assert asbTerminateUWPApplicationOutput == [b'The "terminatePackageApp" action will be completed on next execution.'], \
        "Unexpected .terminatepackageapp output:\r\n%s" % \
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbTerminateUWPApplicationOutput);

