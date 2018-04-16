def cCdbWrapper_fStartUWPApplication(oCdbWrapper, oUWPApplication, sArgument):
  if sArgument is None:
    # Note that the space between the application id and the command-terminating semi-colon MUST be there to
    # make sure the semi-colon is not interpreted as part of the application id!
    sStartUWPApplicationCommand = ".createpackageapp %s %s ;" % \
        (oUWPApplication.sPackageFullName, oUWPApplication.sApplicationId);
    oCdbWrapper.fbFireEvent("Log message", "Starting UWP application", {
      "Application Id": oUWPApplication.sApplicationId, 
      "Package name": oUWPApplication.sPackageName, 
      "Package full name": oUWPApplication.sPackageFullName, 
    });
  else:
    # Note that the space between the argument and the command-terminating semi-colon MUST be there to make
    # sure the semi-colon is not passed to the UWP app as part of the argument!
    sStartUWPApplicationCommand = ".createpackageapp %s %s %s ;" % \
        (oUWPApplication.sPackageFullName, oUWPApplication.sApplicationId, sArgument);
    oCdbWrapper.fbFireEvent("Log message", "Starting UWP application", {
      "Application Id": oUWPApplication.sApplicationId, 
      "Package name": oUWPApplication.sPackageName, 
      "Package full name": oUWPApplication.sPackageFullName, 
      "Argument": sArgument,
    });
  asStartUWPApplicationOutput = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = sStartUWPApplicationCommand,
    sComment = "Start UWP application %s" % oUWPApplication.sPackageName,
  );
  assert asStartUWPApplicationOutput == ["Attach will occur on next execution"], \
      "Unexpected .createpackageapp output: %s" % repr(asStartUWPApplicationOutput);
