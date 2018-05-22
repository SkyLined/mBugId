import re;

gsrIgnoredErrors = r"^(Couldn't resolve error at .*|Ambiguous symbol error at '.+')$";
def cProcess_fuGetAddressForSymbol(oProcess, sSymbol):
  # Get the address of the symbol without the offset:
  asCommandOutput = oProcess.fasExecuteCdbCommand(
    sCommand = '.printf "%%p\\n", @!"%s";' % sSymbol,
    sComment = "Get address for symbol",
    srIgnoredErrors = gsrIgnoredErrors,
  );
  uValueAtIndex = 0;
  if len(asCommandOutput) == 2 and asCommandOutput[0].startswith("Unable to read dynamic function table entry at "):
    # It looks like we can safely ignore this error: the next line should contain the value.
    uValueAtIndex = 1;
  else:
    assert len(asCommandOutput) == 1, \
        "Expected only one line in value result:\r\n%s" % "\r\n".join(asCommandOutput);
  if re.match(gsrIgnoredErrors, asCommandOutput[uValueAtIndex]):
    return None;
  try:
    return long(asCommandOutput[uValueAtIndex], 16);
  except:
    raise AssertionError("Cannot parse value %s for %s on line %s: %s\r\n%s" % \
        (repr(asCommandOutput[uValueAtIndex]), repr(sSymbol), uValueAtIndex + 1, asCommandOutput[uValueAtIndex], \
        "\r\n".join(asCommandOutput)));
