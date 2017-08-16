import re;

def cProcess_fuGetValue(oProcess, sValue, sComment):
  if re.match(r"^@[\w\$].+$", sValue):
    # @reg or @$pseudo_reg
    return oProcess.fuGetValueForRegister(sValue, sComment);
  
  asCommandOutput = oProcess.fasExecuteCdbCommand(
    sCommand = '.printf "%%p\\n", %s;' % sValue,
    sComment = sComment,
    srIgnoreErrors = r"^(Couldn't resolve error at .*|Ambiguous symbol error at '.+')$",
  );
  if asCommandOutput is None:
    return None;
  uValueAtIndex = 0;
  if len(asCommandOutput) == 2 and asCommandOutput[0].startswith("Unable to read dynamic function table entry at "):
    # It looks like we can safely ignore this error: the next line should contain the value.
    uValueAtIndex = 1;
  else:
    assert len(asCommandOutput) == 1, \
        "Expected only one line in value result:\r\n%s" % "\r\n".join(asCommandOutput);
  if asCommandOutput[uValueAtIndex].startswith("Couldn't resolve error at "):
    return None;
  try:
    return long(asCommandOutput[uValueAtIndex], 16);
  except:
    raise AssertionError("Cannot parse value %s for %s on line %s: %s\r\n%s" % \
        (repr(asCommandOutput[uValueAtIndex]), repr(sValue), uValueAtIndex + 1, asCommandOutput[uValueAtIndex], \
        "\r\n".join(asCommandOutput)));
