import re;

def cProcess_fdsSymbol_by_uAddressForPartialSymbol(oProcess, sPartialSymbol, sComment):
  asCommandOutput = oProcess.fasExecuteCdbCommand(
    sCommand = 'x %s;' % sPartialSymbol,
    sComment = sComment,
  );
  dsSymbol_by_uAddress = [];
  for sLine in asCommandOutput:
    oValueMatch = re.match("^([0-9`a-f]+)\s+(.+?)$", sLine);
    assert oValueMatch, \
        "Cannot parse 'x' command output for partial symbol %s on line %d: %s\r\n%s" % \
        (repr(sPartialSymbol), len(auValues) + 1, sLine, "\r\n".join(asCommandOutput));
    sAddress, sSymbol = oValueMatch.groups();
    dsSymbol_by_uAddress[long(sAddress.replace("`", ""), 16)] = sSymbol;
  return auValues;