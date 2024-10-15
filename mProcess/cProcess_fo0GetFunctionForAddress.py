def cProcess_fo0GetFunctionForAddress(oProcess, uAddress):
  sb0Symbol = oProcess.fsb0GetSymbolForAddress(uAddress, b"Get function symbol for address 0x%X" % uAddress);
  if sb0Symbol is None:
    return None;
  (
    u0Address,
    sb0UnloadedModuleFileName, o0Module, u0ModuleOffset,
    o0Function, i0OffsetFromStartOfFunction
  ) = oProcess.ftxSplitSymbolOrAddress(sb0Symbol);
  return o0Function;