import re;

def cCdbWrapper_fHandleDebugOutputFromApplication(oCdbWrapper, asOutputWhileRunningApplication):
  if oCdbWrapper.oCdbCurrentProcess.uId == oCdbWrapper.oUtilityProcess.uId:
    return; # We do not expect these but if we do see them, they should be ignored.
  # Unfortunately, cdb outputs text whenever an ignored first chance exception happens and I cannot find out how to
  # silence it. So, we'll have to remove these from the output, which is sub-optimal, but should work well enough
  # for now. Also, page heap outputs stuff that we don't care about as well, which we hide here.
  asDebugOutput = [
    sLine for sLine in asOutputWhileRunningApplication
    if not re.match("^(%s)$" % "|".join([
      r"\(\w+\.\w+\): Unknown exception \- code \w{8} \(first chance\)",
      r"Page heap: pid 0x\w+: page heap enabled with flags 0x\w+\.",
    ]), sLine)
  ];
  if asDebugOutput:
    # It could be that the output was from page heap, in which case no event is fired.
    oCdbWrapper.fbFireCallbacks("Application debug output", oCdbWrapper.oCdbCurrentProcess, asDebugOutput);
