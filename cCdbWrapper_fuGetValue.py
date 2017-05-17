import re;

def cCdbWrapper_fuGetValue(oCdbWrapper, sValue, sComment):
  if re.match(r"^@\$?\w+$", sValue):
    # This is a register or pseudo-register: it's much faster to get these using the "r" command than printing them
    # as is done for other values:
    asValueResult = oCdbWrapper.fasSendCommandAndReadOutput('r %s; $$ %s' % (sValue, sComment));
    assert len(asValueResult) == 1, \
        "Expected only one line in value result:\r\n%s" % "\r\n".join(asValueResult);
    sValueResult = asValueResult[0];
    assert sValueResult.lower().startswith(sValue[1:].lower() + "="), \
        "Expected result to start with %s\r\n%s" % (repr(sValue[1:].lower() + "="), "\r\n".join(asValueResult));
    try:
      return long(sValueResult[len(sValue):], 16);
    except:
      raise AssertionError("Cannot parse value %s for %s:\r\n%s" % (repr(sValueResult[len(sValue):]), sValue, "\r\n".join(asValueResult)));
  asValueResult = oCdbWrapper.fasSendCommandAndReadOutput('.printf "%%p\\n", %s; $$ %s' % (sValue, sComment),
      srIgnoreErrors = r"^Couldn't resolve error at .*$");
  if asValueResult is None:
    return None;
  uValueAtIndex = 0;
  if len(asValueResult) == 2 and asValueResult[0].startswith("Unable to read dynamic function table entry at "):
    # It looks like we can safely ignore this error: the next line should contain the value.
    uValueAtIndex = 1;
  elif len(asValueResult) == 2 and asValueResult[0] == "WARNING: Stack overflow detected. The unwound frames are extracted from outside normal stack bounds.":
    # It looks like we can safely ignore this warning: the next line should contain the value.
    uValueAtIndex = 1;
  else:
    assert len(asValueResult) == 1, \
        "Expected only one line in value result:\r\n%s" % "\r\n".join(asValueResult);
  if asValueResult[uValueAtIndex].startswith("Couldn't resolve error at "):
    return None;
  try:
    return long(asValueResult[uValueAtIndex], 16);
  except:
    raise AssertionError("Cannot parse value for %s on line %s:\r\n%s" % (sValue, uValueAtIndex + 1, "\r\n".join(asValueResult)));
