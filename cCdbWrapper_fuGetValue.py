def cCdbWrapper_fuGetValue(oCdbWrapper, sValue):
  asValueResult = oCdbWrapper.fasSendCommandAndReadOutput(
      '.printf "%%p\\n", %s; $$ Get value' % sValue, bIgnoreUnknownSymbolErrors = True);
  if not oCdbWrapper.bCdbRunning: return;
  if len(asValueResult) > 1 and asValueResult[-1].startswith("Ambiguous symbol error at '"):
    return None;
  uValueAtIndex = 0;
  if len(asValueResult) == 2 and asValueResult[0].startswith("Unable to read dynamic function table entry at "):
    # It looks like we can safely ignore this error: the next line should contain the value.
    uValueAtIndex = 1;
  elif len(asValueResult) == 2 and asValueResult[0] == "WARNING: Stack overflow detected. The unwound frames are extracted from outside normal stack bounds."):
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
