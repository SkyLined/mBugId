import re;

from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..mCP437 import fsCP437FromBytesString;

grbInvalidSymbolErrors = re.compile(rb"^(Couldn't resolve error at .*|Ambiguous symbol error at '.+')$");

def cProcess_fu0GetAddressForSymbol(oSelf, sbSymbol):
  assert sbSymbol[0] not in b"0123456789", \
      "You should not pass a number (%s) as a symbol" % repr(sbSymbol)[1:];
  # Get the address of the symbol without the offset:
  asbCommandOutput = oSelf.fasbExecuteCdbCommand(
    sbCommand = b'.printf "%%p\\n", @!"%s";' % sbSymbol,
    sb0Comment = b"Get address for symbol",
  );
  if len(asbCommandOutput) == 2 and asbCommandOutput[0].startswith(b"Unable to read dynamic function table entry at "):
    # It looks like we can safely ignore this error: the next line should contain the value.
    asbCommandOutput.pop(0);
  else:
    assert len(asbCommandOutput) == 1, \
        "Expected only one line in value result:\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCommandOutput);
  if grbInvalidSymbolErrors.match(asbCommandOutput[0]):
    return None;
  return fu0ValueFromCdbHexOutput(asbCommandOutput[0]);
