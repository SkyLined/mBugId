from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..rbSymbolOrAddress import rbSymbolOrAddress;

def cProcess_ftxSplitSymbolOrAddress(oProcess, sbSymbolOrAddress):
  obSymbolOrAddressMatch = rbSymbolOrAddress.match(sbSymbolOrAddress);
  assert obSymbolOrAddressMatch, \
      "Symbol or address does not match a known format: %s" % repr(sbSymbolOrAddress);
  (
    sb0Address,
    sb0UnloadedModuleFileName, sb0UnloadedModuleOffset,
    sb0ModuleCdbIdOrAddress, sb0ModuleOffset,
    sb0FunctionSymbol, sbPlusOrMinusOffset, sb0OffsetInFunction,
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
  elif sb0ModuleCdbIdOrAddress == b"SharedUserData":
    # "ShareUserData" is a symbol outside of any module that gets used as a module name in cdb.
    # Any value referencing it will be converted to an address:
    u0Address = oProcess.fu0GetAddressForSymbol(b"%s!%s" % (sb0ModuleCdbIdOrAddress, sb0FunctionSymbol));
    if u0Address and u0ModuleOffset: u0Address += u0ModuleOffset;
  else:
    sbModuleCdbId = sb0ModuleCdbIdOrAddress;
    o0Module = oModule = oProcess.fo0GetModuleForCdbId(sbModuleCdbId);
    if sb0FunctionSymbol is not None:
      o0Function = oModule.foGetOrCreateFunctionForSymbol(sb0FunctionSymbol);
      i0OffsetFromStartOfFunction = (
        0 if sb0OffsetInFunction is None else
        fu0ValueFromCdbHexOutput(sb0OffsetInFunction) * (1 if sbPlusOrMinusOffset == b"+" else -1)
      );
  return (
    u0Address,
    sb0UnloadedModuleFileName, o0Module, u0ModuleOffset,
    o0Function, i0OffsetFromStartOfFunction
  );