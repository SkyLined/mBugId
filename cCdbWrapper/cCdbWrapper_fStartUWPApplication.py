from mNotProvided import fAssertType;

def cCdbWrapper_fStartUWPApplication(oCdbWrapper, oUWPApplication, sb0Argument):
  fAssertType("sb0Argument", sb0Argument, bytes, None);
  sbPackageName = bytes(oUWPApplication.sPackageName, "ascii", "strict");
  sbPackageFullName = bytes(oUWPApplication.sPackageFullName, "ascii", "strict");
  sbApplicationId = bytes(oUWPApplication.sApplicationId, "ascii", "strict");
  if sb0Argument is None:
    # Note that the space between the application id and the command-terminating semi-colon MUST be there to
    # make sure the semi-colon is not interpreted as part of the application id!
    sbStartUWPApplicationCommand = b".createpackageapp %s %s ;" % \
        (sbPackageFullName, sbApplicationId);
    oCdbWrapper.fbFireCallbacks("Log message", "Starting UWP application", {
      "Application Id": oUWPApplication.sApplicationId, 
      "Package name": oUWPApplication.sPackageName, 
      "Package full name": oUWPApplication.sPackageFullName, 
    });
  else:
    # Note that the space between the argument and the command-terminating semi-colon MUST be there to make
    # sure the semi-colon is not passed to the UWP app as part of the argument!
    sbStartUWPApplicationCommand = b".createpackageapp %s %s %s ;" % \
        (sbPackageFullName, sbApplicationId, sb0Argument);
    oCdbWrapper.fbFireCallbacks("Log message", "Starting UWP application", {
      "Application Id": oUWPApplication.sApplicationId, 
      "Package name": oUWPApplication.sPackageName, 
      "Package full name": oUWPApplication.sPackageFullName, 
      "Argument": sb0Argument,
    });
  asbStartUWPApplicationOutput = oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = sbStartUWPApplicationCommand,
    sb0Comment = b"Start UWP application %s" % sbPackageName,
  );
  assert asbStartUWPApplicationOutput == [b"Attach will occur on next execution"], \
      "Unexpected .createpackageapp output: %s" % repr(asbStartUWPApplicationOutput);
