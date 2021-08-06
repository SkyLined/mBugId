import re;

grbVFTableSymbolClassName = re.compile(
  rb"^"                                       
  rb"[0-9`A-F]+"                              # number
  rb"\s*"                                     # whitespace
  rb"[0-9`A-F\?]+"                            # number
  rb"\s+"                                     # whitespace
  rb"\w+" rb"!" rb"(.+?)" rb"::`vftable'"     # module "!" **classname** "::`vftable'"
  rb"\s*$",                                   # optional whitespace
  re.I
)

def fsbGetCPPObjectClassNameFromVFTable(oProcess, uCPPObjectAddress):
  # A C++ object is store in memory starting with a pointer to its virtual function table.
  # The symbol for this virtual function table should follow the pattern "module![namespace::]classname::`vftable'"
  # We can extract the classname from this symbol.
  asbVFTableSymbolOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b"dps 0x%X L1;" % uCPPObjectAddress,
    sb0Comment = b"Get C++ vftable pointer symbol",
    bOutputIsInformative = True,
  );
  assert len(asbVFTableSymbolOutput) == 1, \
      "Unexpected vftable pointer symbol output:\r\n%s" % "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbVFTableSymbolOutput);
  obVFTableSymbolClassNameMatch = grbVFTableSymbolClassName.match(asbVFTableSymbolOutput[0]);
  return obVFTableSymbolClassNameMatch.group(1) if obVFTableSymbolClassNameMatch else None;
