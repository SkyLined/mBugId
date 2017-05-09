import re;

def cCdbWrapper_fsGetUnicodeString(oCdbWrapper, uAddress, sComment):
  asGetStringOutput = oCdbWrapper.fasSendCommandAndReadOutput(
    ".if ($vvalid(0x%X, 1) {.printf \"%mu\\r\\n1\\r\\n\", 0x%X}; .else .printf \"0\\r\\n\"; $$ %s" % (uAddress, uAddress, sComment)
  );
  sSuccess = asGetStringOutput[-1];
  if sSuccess == "0":
    assert len(asGetStringOutput) == 1, \
        "Unexpected string output:\r\n%s" % "\r\n".join(asGetStringOutput);
    return None;
  assert sSuccess == "1", \
      "Unexpected string output:\r\n%s" % "\r\n".join(asGetStringOutput);
  return "\r\n".join(asGetStringOutput[:-1]);
