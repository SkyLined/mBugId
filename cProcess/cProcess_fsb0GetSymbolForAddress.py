import re;

from ..dxConfig import dxConfig;
from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..rbSymbolOrAddress import rbSymbolOrAddress;
from ..mCP437 import fsCP437FromBytesString;

grbAddress = re.compile(
  rb"\A"
  rb"[0-9`a-f]+"              # address
  rb"\Z"
);
grbSymbolWithOrWithoutAddress = re.compile(
  rb"\A"
  rb"(.*?)"                   # symbol
  rb"(?:"                     # optional {
    rb"\s+" rb"\<PERF\>"      #   whitespace "<PERF>" 
  rb")?"                      # }
  rb"(?:"                     # optional {
    rb"\s+" rb"\("            #   whitespace "(" 
      rb"\w+"                 #   module cdb id
      rb"\+0x"                #   "+0x"
      rb"(?:[0-9`a-f]+?)"     #   offset
    rb"\)"                    #   ")"
  rb")?"                      # }
  rb"(?:"                     # optional {
    rb"\s+" rb"\("            #   whitespace "(" 
      rb"(?:[0-9`a-f]+?)"     #   address
    rb"\)"                    #   ")"
  rb")?"                      # }
  rb"\Z"
);


def cProcess_fsb0GetSymbolForAddress(oProcess, uAddress, sbAddressDescription):
  oProcess.fLoadSymbols();
  # Output for an invalid (NULL) pointer:
  #   >00000000
  # Output for a module without symbol information (in x64 debugger):
  #   >nmozglue+0xf0c4 (73f1f0c4)
  # Output for a valid symbol (in x86 debugger, notice different header aligning):
  #   >ntdll!DbgBreakPoint (77ec1250)
  if uAddress < dxConfig["uMaxAddressOffset"]:
    return None; # quick return for NULL pointers
  sbGetSymbolCommand = b'.printf "%%y\\n", 0x%X;' % uAddress;
  asbSymbolOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = sbGetSymbolCommand, 
    sb0Comment = b"Get symbol for %s" % (sbAddressDescription,),
  );
  # If the output contains more than one line, it must be caused by symbol loading; try again.
  assert len(asbSymbolOutput) == 1, \
      "Invalid symbol output:\n%s" % "\n".join(repr(sbLine) for sbLine in asbSymbolOutput);
  # If there is no symbol at the addres, only the address will be output; return None:
  if grbAddress.match(asbSymbolOutput[0]) and fu0ValueFromCdbHexOutput(asbSymbolOutput[0]) == uAddress:
    return None;
  oSymbolWithOrWithoutAddressMatch = grbSymbolWithOrWithoutAddress.match(asbSymbolOutput[0]);
  assert oSymbolWithOrWithoutAddressMatch, \
      "This should always match!"; # By design - something is very broken if not.
  # See if the output contains something we recognize as a symbol; return it.
  sbSymbol = oSymbolWithOrWithoutAddressMatch.group(1);
  o0SymbolMatch = rbSymbolOrAddress.match(sbSymbol);
  if o0SymbolMatch:
    return sbSymbol;
  raise AssertionError(
    "Cannot process get symbol output for address 0x%X:\r\n%s" % (
      uAddress,
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbSymbolOutput),
    )
  );
