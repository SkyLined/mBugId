import re;

from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;

grbSymbolOrAddress = re.compile(
  rb"^\s*"                                      # optional whitespace
  rb"(?:"                                       # either {
    rb"0x"                                      #   "0x"
    rb"([0-9`a-f]+)"                            #   <<<address>>>
  rb"|"                                         # } or {
    rb"<Unloaded_"                              #   "<Unloaded_"
    rb"(.*)"                                    #   <<<module file name>>>
    rb">"                                       #   ">"
    rb"(?:"                                     #   optional{
      rb"\+0x0*" rb"([0-9`a-f]+?)"              #     "+0x" "0"... <<<hex offset in unloaded module>>>
    rb")?"                                      #   }
  rb"|"                                         # } or {
    rb"(\w+)"                                   #   <<<cdb module id>>>
    rb"(?:"                                     #   optional either {
      rb"\+0x0*" rb"([0-9`a-f]+?)"              #     "+0x" "0"... <<<hex offset in module>>>
    rb"|"                                       #   } or {
      rb"!" rb"(.+?)"                           #     "!" <<<function name>>>
      rb"(?:"                                   #     optional {
      rb"([\+\-])" rb"0x0*" rb"([0-9`a-f]+?)"   #       ["+" or "-"] "0x" "0"... <<<hex offset in function>>>
      rb")?"                                    #     }
    rb")?"                                      #   }
  rb")"                                         # }
  rb"\s*$"                                      # optional whitespace
);

def cProcess_ftxSplitSymbolOrAddress(oProcess, sbSymbolOrAddress):
  obSymbolOrAddressMatch = grbSymbolOrAddress.match(sbSymbolOrAddress);
  assert obSymbolOrAddressMatch, \
      "Unknown symbol or address format: %s" % repr(sbSymbolOrAddress);
  (
    sb0Address,
    sb0UnloadedModuleFileName, sb0UnloadedModuleOffset,
    sb0ModuleCdbId, sb0ModuleOffset,
    sb0FunctionSymbol, sbPlusOrMinusOffset, sb0OffsetInFunction
  ) = obSymbolOrAddressMatch.groups();
  u0Address = None;
  o0Module = None;
  u0ModuleOffset = fu0ValueFromCdbHexOutput(sb0ModuleOffset);
  o0Function = None;
  i0OffsetFromStartOfFunction = None;
  if sb0Address is not None:
    u0Address = fu0ValueFromCdbHexOutput(sb0Address);
  elif sb0UnloadedModuleFileName is not None:
    # sb0UnloadedModuleFileName is returned without modification
    u0ModuleOffset = fu0ValueFromCdbHexOutput(sb0UnloadedModuleOffset);
  elif sb0ModuleCdbId == b"SharedUserData":
    # "ShareUserData" is a symbol outside of any module that gets used as a module name in cdb.
    # Any value referencing it will be converted to an address:
    u0Address = oProcess.fuGetAddressForSymbol(b"%s!%s" % (sb0ModuleCdbId, sb0FunctionSymbol));
    if u0ModuleOffset: uAddress += u0ModuleOffset;
  else:
    o0Module = oProcess.foGetOrCreateModuleForCdbId(sb0ModuleCdbId);
    if sb0FunctionSymbol is not None:
      o0Function = o0Module.foGetOrCreateFunctionForSymbol(sb0FunctionSymbol);
      i0OffsetFromStartOfFunction = (
        0 if sb0OffsetInFunction is None else
        fu0ValueFromCdbHexOutput(sb0OffsetInFunction) * (1 if sbPlusOrMinusOffset == b"+" else -1)
      );
  return (
    u0Address,
    sb0UnloadedModuleFileName, o0Module, u0ModuleOffset,
    o0Function, i0OffsetFromStartOfFunction
  );