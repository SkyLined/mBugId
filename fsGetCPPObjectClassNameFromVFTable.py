import re;

def fsGetCPPObjectClassNameFromVFTable(oCdbWrapper, uCPPObjectAddress):
  # A C++ object is store in memory starting with a pointer to its virtual function table.
  # The symbol for this virtual function table should follow the pattern "module![namespace::]classname::`vftable'"
  # We can extract the classname from this symbol.
  asVFTableSymbolOutput = oCdbWrapper.fasExecuteCdbCommand(
    sCommand = "dps 0x%X L1;" % uCPPObjectAddress,
    sComment = "Get C++ vftable pointer symbol",
    bOutputIsInformative = True,
  );
  assert len(asVFTableSymbolOutput) == 1, \
      "Unexpected vftable pointer symbol output:\r\n%s" % "\r\n".join(asVFTableSymbolOutput);
  oVFTableSymbolMatch = re.match(r"^[0-9`A-F]+\s*[0-9`A-F\?]+(?:\s+(.+?))?\s*$", asVFTableSymbolOutput[0], re.I);
  assert oVFTableSymbolMatch, \
      "Unexpected vftable pointer symbol output:\r\n%s" % "\r\n".join(asVFTableSymbolOutput);
  sVFTableSymbol = oVFTableSymbolMatch.group(1);
  if sVFTableSymbol is None:
    return None; # There is no symbol at this address.
  oClassNameMatch = re.match(r"^\w+!(.+?)::`vftable'$", oVFTableSymbolMatch.group(1));
  if oClassNameMatch is None:
    return None; # The symbol does not follow the pattern we're looking for.
  return oClassNameMatch.group(1);
