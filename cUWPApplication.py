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
    # Output should consist of "Name : Value" Pairs. Values can be lists that span multiple lines. In this case
    # the value starts with "{" and each line ends with "," except the last line which ends with "}"
    bInCurlyBraceList = False;
    bNameChecked = False;
    for sLine in asQueryOutput:
      if sLine:
        if bInCurlyBraceList:
          # 
          oValueMatch = re.match(r"^ (.*)[,}]$", sLine);
          assert oValueMatch, \
              "Unrecognized Get-AppxPackage output: %s in\r\n%s" % (repr(sLine), "\r\n".join(asQueryOutput));
          sValue, sLineEnd = oValueMatch.groups();
          bInCurlyBraceList = sLineEnd == ",";
        else:
          oNameAndValueMatch = re.match(r"^(.*?)\s* : (\{)?(.*?)$", sLine);
          assert oNameAndValueMatch, \
              "Unrecognized Get-AppxPackage output: %s in\r\n%s" % (repr(sLine), "\r\n".join(asQueryOutput));
        sName, sCurlyBrace, sValue = oNameAndValueMatch.groups();
        if sCurlyBrace:
          assert sValue[-1] in ",}", \
              "Expected comma or end of curly brace list: %s in\r\n%s" %  (repr(sLine), "\r\n".join(asQueryOutput));
          bInCurlyBraceList = sValue[-1] == ",";
          sValue = sValue[:-1];
        if sName == "Name":
          assert not bInCurlyBraceList, \
              "The package name is not supposed to be a list";
          assert sValue.lower() == oUWPApplication.sPackageName.lower(), \
              "Expected application package name to be %s, but got %s.\r\n%s" % \
              (oUWPApplication.sPackageName, sValue, "\r\n".join(asQueryOutput));
          bNameChecked = True;
        elif sName == "PackageFullName":
          assert not bInCurlyBraceList, \
              "The package full name is not supposed to be a list";
          oUWPApplication.sPackageFullName = sValue;
        elif sName == "PackageFamilyName":
          assert not bInCurlyBraceList, \
              "The package family name is not supposed to be a list";
          oUWPApplication.sPackageFamilyName = sValue;
    assert bNameChecked, \
        "Expected Get-AppxPackage output to contain 'Name' value.\r\n%s" % "\r\n".join(asQueryOutput);
    assert oUWPApplication.sPackageFullName, \
        "Expected Get-AppxPackage output to contain 'PackageFullName' value.\r\n%s" % "\r\n".join(asQueryOutput);
    assert oUWPApplication.sPackageFamilyName, \
        "Expected Get-AppxPackage output to contain 'PackageFamilyName' value.\r\n%s" % "\r\n".join(asQueryOutput);
    
    # Sanity check the application id
    asApplicationIds = fasRunApplication("powershell", "(Get-AppxPackageManifest %s).package.applications.application.id" % oUWPApplication.sPackageFullName);
    assert sApplicationId in asApplicationIds, \
        "The specified application id (%s) does not appear to exist (known ids: %s)" % (repr(sApplicationId), ", ".join([repr(s) for s in asApplicationIds]));
