import re;

from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..rbSymbolOrAddress import rbSymbolOrAddress;

def cProcess_ftxSplitSymbolOrAddress(oProcess, sbSymbolOrAddress):
  obSymbolOrAddressMatch = rbSymbolOrAddress.match(sbSymbolOrAddress);
  assert obSymbolOrAddressMatch, \
      "Symbol or address does not match a known format: %s" % repr(sbSymbolOrAddress);
  (
    sb0UnloadedModuleFileName, sb0UnloadedModuleOffset,
    sb0ModuleCdbIdOrAddress, sb0ModuleOffset,
    sb0FunctionSymbol, sbPlusOrMinusOffset, sb0OffsetInFunction,
    sb0Address,
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
  elif sb0ModuleCdbIdOrAddress[0] in b"0123456789":
    # Address are hexadecimal (i.e. start with "0x"), or (unlikely) decimal.
    # Either way they start with a digit. cdb ids for modules are assumed to
    # never start with a digit, so if the first char is a digit, it must be
    # and address.
    # TODO: confirm this is true by loading a module "1test.dll"
    # and find out what id cdb gives this module.
    u0Address = fu0ValueFromCdbHexOutput(sb0ModuleCdbIdOrAddress);
  else:
    o0Module = oProcess.fo0GetModuleForCdbId(sb0ModuleCdbIdOrAddress);
    assert o0Module, \
        "Cannot find module %s!?" % repr(sb0ModuleCdbIdOrAddress)[1:];
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