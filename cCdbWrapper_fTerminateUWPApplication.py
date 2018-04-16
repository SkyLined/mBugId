def cCdbWrapper_fTerminateUWPApplication(oCdbWrapper, oUWPApplication):
  oCdbWrapper.fbFireEvent("Log message", "Terminating UWP application", {
    "Application Id": oUWPApplication.sApplicationId, 
    "Package name": oUWPApplication.sPackageName, 
    "Package full name": oUWPApplication.sPackageFullName, 
  });
  # Kill it so we are sure to run a fresh copy.
  asTerminateUWPApplicationOutput = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = ".terminatepackageapp %s;" % oUWPApplication.sPackageFullName,
    sComment = "Terminate UWP application %s" % oUWPApplication.sPackageName,
  );
  if asTerminateUWPApplicationOutput:
    assert asTerminateUWPApplicationOutput == ['The "terminatePackageApp" action will be completed on next execution.'], \
        "Unexpected .terminatepackageapp output:\r\n%s" % "\r\n".join(asTerminateUWPApplicationOutput);

