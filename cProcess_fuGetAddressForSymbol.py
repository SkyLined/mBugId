import re;

from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;

grbIgnoredErrors = re.compile(rb"^(Couldn't resolve error at .*|Ambiguous symbol error at '.+')$");

def cProcess_fuGetAddressForSymbol(oProcess, sbSymbol):
  # Get the address of the symbol without the offset:
  asbCommandOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b'.printf "%%p\\n", @!"%s";' % sbSymbol,
    sb0Comment = b"Get address for symbol",
    rb0IgnoredErrors = grbIgnoredErrors,
  );
  uValueAtIndex = 0;
  if len(asbCommandOutput) == 2 and asbCommandOutput[0].startswith(b"Unable to read dynamic function table entry at "):
    # It looks like we can safely ignore this error: the next line should contain the value.
    uValueAtIndex = 1;
  else:
    assert len(asbCommandOutput) == 1, \
        "Expected only one line in value result:\r\n%s" % \
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbCommandOutput);
  if grbIgnoredErrors.match(asbCommandOutput[uValueAtIndex]):
    return None;
  try:
    return fu0ValueFromCdbHexOutput(asbCommandOutput[uValueAtIndex]);
  except:
    raise AssertionError(
      "Cannot parse value %s for %s on line %s: %s\r\n%s" % (
        repr(asbCommandOutput[uValueAtIndex]),
        repr(sbSymbol),
        uValueAtIndex + 1,
        asbCommandOutput[uValueAtIndex],
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbCommandOutput)
      )
    );
