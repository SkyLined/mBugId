import re;

def cProcess_fsGetUnicodeString(oProcess, sAddress, sComment):
  return cProcess_fsGet_String(oProcess, sAddress, sComment, True);
def cProcess_fsGetASCIIString(oProcess, sAddress, sComment):
  return cProcess_fsGet_String(oProcess, sAddress, sComment, False);

def cProcess_fsGet_String(oProcess, sAddress, sComment, bUnicode):
  asCommandOutput = oProcess.fasExecuteCdbCommand(
    sCommand = ".if ($vvalid(0x%X, 1) {.printf \"%s\\r\\n1\\r\\n\", 0x%X}; .else .printf \"0\\r\\n\";" % \
        (uAddress, (bUnicode and "%mu" or "%ma", sAddress), uAddress),
    sComment = sComment,
    srIgnoreErrors = r"^Couldn't resolve error at .*$",
  );
  sSuccess = asGetStringOutput[-1];
  if sSuccess == "0":
    assert len(asGetStringOutput) == 1, \
        "Unexpected string output:\r\n%s" % "\r\n".join(asGetStringOutput);
    return None;
  assert sSuccess == "1", \
      "Unexpected string output:\r\n%s" % "\r\n".join(asGetStringOutput);
  uValueAtIndex = 0;
  if len(asCommandOutput) > 1 and asCommandOutput[0].startswith("Unable to read dynamic function table entry at "):
    # It looks like we can safely ignore this error: the next line should contain the value.
    uValueAtIndex = 1;
  return "\r\n".join(asCommandOutput[uValueAtIndex:-1]);
