import re;

from mRegistry import cRegistryHiveKey;

# Cache which binaries have page heap enabled/disabled. this assumes that the user does not modify the page heap
# settings while BugId is running.
gdbPageHeapEnabled_by_sBinaryName = {};
guRequiredFlags = 0x02109870;

def cProcess_fEnsurePageHeapIsEnabled(oProcess):
  if oProcess.bPageHeapEnabled is not None:
    return; # We have ensured this before.
  if oProcess.sBinaryName in gdbPageHeapEnabled_by_sBinaryName:
    oProcess.bPageHeapEnabled = gdbPageHeapEnabled_by_sBinaryName[oProcess.sBinaryName];
    return;
  oRegistryHiveKey = cRegistryHiveKey(
    sHiveName = "HKLM",
    sKeyPath = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\%s" % oProcess.sBinaryName,
  );
  o0GlobalFlags = oRegistryHiveKey.fo0GetValueForName("GlobalFlag");
  if o0GlobalFlags and o0GlobalFlags.sTypeName == "REG_SZ" and re.match("^0x[0-9a-fA-F]{8}$", o0GlobalFlags.xValue):
    uValue = int(o0GlobalFlags.xValue[2:], 16);
    if uValue & guRequiredFlags == guRequiredFlags:
      # Page heap is enabled with all the required options:
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
  # NOTE: DISABLED TO AVOID ACCESSING oMainModule before the process is fully loaded.
  bPreventable = True;#re.match(rb"image[0-9a-f]{8}", oProcess.oMainModule.sbCdbId, re.I) is None;
  # Report it
  if not oProcess.oCdbWrapper.fbFireCallbacks("Page heap not enabled", oProcess, bPreventable):
    # This is fatal if it's preventable and there is no callback handler
    assert not bPreventable, \
        "Full page heap is not enabled for %s in process 0x%X." % (oProcess.sBinaryName, oProcess.uId);
