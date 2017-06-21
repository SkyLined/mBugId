import os, re;

gsDebuggerExtensionBinBasePath = os.path.abspath(os.path.join(os.path.dirname(__file__), "DebuggerExtension", "bin"));
gdsDebuggerExtensionDLLPath_by_sCdbISA = {
  "x86": os.path.join(gsDebuggerExtensionBinBasePath, "i386", "debugext.dll"),
  "x64": os.path.join(gsDebuggerExtensionBinBasePath, "amd64", "debugext.dll"),
};

class cDebuggerExtension(object):
  @staticmethod
  def foLoad(oCdbWrapper):
    sDebuggerExtensionDLLPath = gdsDebuggerExtensionDLLPath_by_sCdbISA[oCdbWrapper.sCdbISA];
    asLoadOutput = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = '.load "%s";' % sDebuggerExtensionDLLPath.replace("\\", "\\\\").replace('"', '\\"'),
      sComment = "Load debugger extension",
    );
    assert not asLoadOutput, \
        "Failed to load debugger extension %s:\r\n%s" % (sDebuggerExtensionDLLPath, "\r\n".join(asLoadOutput));
    return cDebuggerExtension(oCdbWrapper);
  
  def __init__(oDebuggerExtension, oCdbWrapper):
    oDebuggerExtension.oCdbWrapper = oCdbWrapper;
  
  def fuSetVirtualAllocationProtection(oDebuggerExtension, uAddress, uSize, uProtection, sComment):
    oCdbWrapper = oDebuggerExtension.oCdbWrapper;
    assert ";" not in sComment, \
        "Comments cannot have a semi-colon: %s" % repr(sComment);
    asProtectResult = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = "!Protect 0x%X 0x%X 0x%X;" % (uAddress, uSize, uProtection),
      sComment = sComment,
    );
    assert len(asProtectResult) > 0, \
        "!Protect did not return any results.";
    if len(asProtectResult) == 1 and re.match(r"^Protect: (OpenProcess|VirtualProtectEx) failed with error code \d+$", asProtectResult[0]):
      return None;
    uOldProtection = None;
    uNewProtection = None;
    assert len(asProtectResult) == 2, \
        "Expected !Protect output to be 2 lines, not %d:\r\n%s" % (len(asProtectResult), "\r\n".join(asProtectResult));
    oNewProtectionMatch = re.match(r"^New protection \((\d+)\)$", asProtectResult[0]); # first line has new protection flag
    assert oNewProtectionMatch and long(oNewProtectionMatch.group(1)) == uProtection, \
        'Expected !Protect output to start with "New protection (number):\r\n%s' % "\r\n".join(asProtectResult);
    oOldProtectionMatch = re.match(r"^Old protection \((\d+)\)$", asProtectResult[1]); # second line has old protection flag
    assert oOldProtectionMatch, \
        'Expected !Protect output to end with "Old protection (number):\r\n%s' % "\r\n".join(asProtectResult);
    return long(oOldProtectionMatch.group(1));
  
