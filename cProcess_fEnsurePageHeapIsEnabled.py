import re;

from mWindowsAPI import foGetRegistryValue;

# Cache which binaries have page heap enabled/disabled. this assumes that the user does not modify the page heap
# settings while BugId is running.
gdbPageHeapEnabled_by_sBinaryName = {};
guRequiredFlags = 0x02109870;

sRegistryKeyBasePath = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options";

def cProcess_fEnsurePageHeapIsEnabled(oProcess):
  if oProcess.bPageHeapEnabled is not None:
    return; # We have ensured this before.
  if oProcess.sBinaryName in gdbPageHeapEnabled_by_sBinaryName:
    oProcess.bPageHeapEnabled = gdbPageHeapEnabled_by_sBinaryName[oProcess.sBinaryName];
    return;
  oGlobalFlags = foGetRegistryValue("HKLM", r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\%s" % oProcess.sBinaryName, "GlobalFlag");
  if oGlobalFlags and oGlobalFlags.sType == "REG_SZ" and re.match("^0x[0-9a-fA-F]{8}$", oGlobalFlags.xValue):
    uValue = long(oGlobalFlags.xValue[2:], 16);
    if uValue & guRequiredFlags == guRequiredFlags:
      # Page heap is not enabled with all the required options:
      gdbPageHeapEnabled_by_sBinaryName[oProcess.sBinaryName] = True;
      oProcess.bPageHeapEnabled = True;
      return;
  # Page heap is not enabled or not all the required options are enabled
  gdbPageHeapEnabled_by_sBinaryName[oProcess.sBinaryName] = False;
  oProcess.bPageHeapEnabled = False;
  # The "id" cdb uses to identify modules in symbols is normally based on the name of the module binary file.
  # However, for unknown reasons, cdb will sometimes use "imageXXXXXXXX", where XXXXXXXX is the hex address at
  # which the module is loaded (this has only been seen on x86 so far). In such cases, page heap appears to be
  # disabled; I believe whatever keeps cdb from determining the module binary's file name is also keeping page heap
  # from doing the same. In such cases, it appears that page heap cannot be enabled by the user, so we'll report it
  # with the second argument as "False" (not preventable).
  bPreventable = re.match(r"image[0-9a-f]{8}", oProcess.oMainModule.sCdbId, re.I) is None;
  # Report it
  if not oProcess.oCdbWrapper.fbFireEvent("Page heap not enabled", oProcess, bPreventable):
    # This is fatal if it's preventable and there is no callback handler
    assert not bPreventable, \
        "Full page heap is not enabled for %s in process %d/0x%X." % (oProcess.sBinaryName, oProcess.uId, oProcess.uId);
