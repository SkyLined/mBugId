import re, subprocess;

def fasRunApplication(*asCommandLine):
  sCommandLine = " ".join([" " in s and '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"') or s for s in asCommandLine]);
  oProcess = subprocess.Popen(
    args = sCommandLine,
    stdin = subprocess.PIPE,
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE,
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP,
  );
  (sStdOut, sStdError) = oProcess.communicate();
  assert not sStdError, \
      "Error running %s:\r\n%s" % (sCommandLine, sStdErr);
  asStdOut = sStdOut.split("\r\n");
  if asStdOut[-1] == "":
    asStdOut.pop();
  return asStdOut;

class cUWPApplication(object):
  def __init__(oUWPApplication, sPackageName, sApplicationId):
    oUWPApplication.sPackageName = sPackageName;
    oUWPApplication.sApplicationId = sApplicationId;
    
    # Find the package full name and family name
    asQueryOutput = fasRunApplication("powershell", "Get-AppxPackage %s" % oUWPApplication.sPackageName);
    for sLine in asQueryOutput:
      if sLine:
        oNameAndValueMatch = re.match(r"^(.*?)\s* : (.*)$", sLine);
        assert oNameAndValueMatch, \
            "Unrecognized Get-AppxPackage output: %s\r\n%s" % (repr(sLine), "\r\n".join(asQueryOutput));
        sName, sValue = oNameAndValueMatch.groups();
        if sName == "Name":
          assert sValue.lower() == oUWPApplication.sPackageName.lower(), \
              "Expected application package name to be %s, but got %s.\r\n%s" % \
              (oUWPApplication.sPackageName, sValue, "\r\n".join(asQueryOutput));
        elif sName == "PackageFullName":
          oUWPApplication.sPackageFullName = sValue;
        elif sName == "PackageFamilyName":
          oUWPApplication.sPackageFamilyName = sValue;
    assert oUWPApplication.sPackageFullName, \
        "Expected Get-AppxPackage output to contain PackageFullName value.\r\n%s" % "\r\n".join(asQueryOutput);
    assert oUWPApplication.sPackageFamilyName, \
        "Expected Get-AppxPackage output to contain PackageFamilyName value.\r\n%s" % "\r\n".join(asQueryOutput);
    
    # Sanity check the application id
    asApplicationIds = fasRunApplication("powershell", "(Get-AppxPackageManifest %s).package.applications.application.id" % oUWPApplication.sPackageFullName);
    assert sApplicationId in asApplicationIds, \
        "The specified application id (%s) does not appear to exist (known ids: %s)" % (repr(sApplicationId), ", ".join([repr(s) for s in asApplicationIds]));
