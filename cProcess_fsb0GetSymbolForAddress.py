import re;

from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;

grbAddress = re.compile(
  rb"\A"
  rb"[0-9`a-f]+"              # address
  rb"\Z"
);
grbSymbolWithOrWithoutAddress = re.compile(
  rb"\A"
  rb"(.*?)"                   # symbol
  rb"(?:"                     # optional {
    rb"\s+" rb"\("            #   whitespace "(" 
      rb"(?:[0-9`a-f]+?)"     #   address
    rb"\)"                    #   ")"
  rb")?"                      # }
  rb"\Z"
);


def fs0ProcessOutputOrThrowExceptionIfItContainsJunk(oProcess, uAddress, asbSymbolOutput):
  assert len(asbSymbolOutput) == 1, \
      "No symbol output";
  # If there is no symbol at the addres, the address will be output, which we
  # can detect, so we can return None:
  if grbAddress.match(asbSymbolOutput[0]) and fu0ValueFromCdbHexOutput(asbSymbolOutput[0]) == uAddress:
    return None;
  o0SymbolWithOrWithoutAddressMatch = grbSymbolWithOrWithoutAddress.match(asbSymbolOutput[0]);
  (sbSymbolWithoutAddress,) = o0SymbolWithOrWithoutAddressMatch.groups();
  # This will throw an exception is the output contains junk.
  txSplitSymbolOrAddress = oProcess.ftxSplitSymbolOrAddress(sbSymbolWithoutAddress);
  assert txSplitSymbolOrAddress[0] is None, \
      "u0Address part of split symbol should always be None here!?";
  return sbSymbolWithoutAddress;

def cProcess_fsb0GetSymbolForAddress(oProcess, uAddress, sbAddressDescription):
  # Ask cdb for the symbol at the given address. This may cause cdb to output all kinds of stuff related to
  # loading symbols, which make the output unparsable. If we cannot parse the output, we try again: the assumption
  # is that the second time around, cdb will have loaded symbols and only the expected symbol will be output.
  # Output for an invalid (NULL) pointer:
  #   >00000000
  # Output for a module without symbol information (in x64 debugger):
  #   >nmozglue+0xf0c4 (73f1f0c4)
  # Output for a valid symbol (in x86 debugger, notice different header aligning):
  #   >ntdll!DbgBreakPoint (77ec1250)
  sbGetSymbolCommand = b'.printf "%%y\\n", 0x%X;' % uAddress;
  asbSymbolOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = sbGetSymbolCommand, 
    sb0Comment = b"Get symbol for %s (first attempt)" % sbAddressDescription,
  );
  try:
    # Check if the output is a valid symbol or address and return the symbol
    # or None respectively. Throw exception if not which we catch to try again.
    return fs0ProcessOutputOrThrowExceptionIfItContainsJunk(oProcess, uAddress, asbSymbolOutput);
  except:
    pass;
  asbSymbolOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = sbGetSymbolCommand, 
    sb0Comment = b"Get symbol for %s (second attempt: cdb may have output symbol loading junk the first time)" % sbAddressDescription,
  );
  try:
    # Check if the output is a valid symbol or address again and return the
    # symbol or None respectively. Throw exception if not which we catch to
    # throw a more informative error:
    return fs0ProcessOutputOrThrowExceptionIfItContainsJunk(oProcess, uAddress, asbSymbolOutput);
  except Exception as oException:
    raise AssertionError(
      "Cannot process get symbol output for %s (%s):\r\n%s" % (
        repr(sbGetSymbolCommand),
        "\r\n".join(str(sbLine, "ascii", "strict") for sbLine in asbSymbolOutput),
        repr(oException),
      )
    );
