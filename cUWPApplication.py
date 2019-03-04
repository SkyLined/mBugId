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
  (sStdOut, sStdErr) = oProcess.communicate();
  assert not sStdErr, \
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
    oUWPApplication.sPackageFullName = None;
    oUWPApplication.sPackageFamilyName = None;
    # Output should consist of "Name : Value" Pairs. Values can span multiple lines in which case additional lines
    # start with a number of spaces. There is never a space before a line that start with "Name :".
    # --- example multi-line output ---
    # Publisher         : CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, 
    #                     S=Washington, C=US
    # ---
    # Dependencies      : {Microsoft.NET.CoreRuntime.1.1_1.1.25915.0_x86__8wekyb3d8bbwe, 
    #                     Microsoft.VCLibs.140.00.Debug_14.0.26428.1_x86__8wekyb3d8bbwe}
    dsValue_by_sName = {};
    sCurrentName = None;
    for sLine in asQueryOutput:
      if sLine:
        if sLine[0] == " ":
          assert sCurrentName is not None, \
              "Get-AppxPackage output firstline starts with a space: %s in\r\n%s" % (repr(sLine), "\r\n".join(asQueryOutput));
          dsValue_by_sName[sCurrentName] += " " + sLine.strip();
        else:
          oNameAndValueMatch = re.match(r"^(.*?)\s+: (.*)$", sLine);
          assert oNameAndValueMatch, \
              "Unrecognized Get-AppxPackage output: %s in\r\n%s" % (repr(sLine), "\r\n".join(asQueryOutput));
          sCurrentName, sValue = oNameAndValueMatch.groups();
          assert sCurrentName not in dsValue_by_sName, \
              "Get-AppxPackage output contains value for %s twice:\r\n%s" % (repr(sCurrentName), "\r\n".join(asQueryOutput));
          dsValue_by_sName[sCurrentName] = sValue;
    sNameValue = dsValue_by_sName.get("Name");
    assert sNameValue, \
        "Expected Get-AppxPackage output to contain 'Name' value.\r\n%s" % "\r\n".join(asQueryOutput);
    assert sNameValue.lower() == oUWPApplication.sPackageName.lower(), \
        "Expected application package name to be %s, but got %s.\r\n%s" % \
        (oUWPApplication.sPackageName, sNameValue, "\r\n".join(asQueryOutput));
    oUWPApplication.sPackageFullName = dsValue_by_sName.get("PackageFullName");
    assert oUWPApplication.sPackageFullName, \
        "Expected Get-AppxPackage output to contain 'PackageFullName' value.\r\n%s" % "\r\n".join(asQueryOutput);
    oUWPApplication.sPackageFamilyName = dsValue_by_sName.get("PackageFamilyName");
    assert oUWPApplication.sPackageFamilyName, \
        "Expected Get-AppxPackage output to contain 'PackageFamilyName' value.\r\n%s" % "\r\n".join(asQueryOutput);
    # Sanity check the application id
    asApplicationIds = fasRunApplication("powershell", "(Get-AppxPackageManifest %s).package.applications.application.id" % oUWPApplication.sPackageFullName);
    assert sApplicationId in asApplicationIds, \
        "The specified application id (%s) does not appear to exist (known ids: %s)" % (repr(sApplicationId), ", ".join([repr(s) for s in asApplicationIds]));
