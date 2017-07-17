import re;

def fxCallModuleAndFunctionFromCallInstructionForReturnAddress(oProcess, uReturnAddress):
  # The symbol may not be correct when using export symbols, or if we're in a small branch that is not marked
  # correctly in the pdb (cdb will report the closest symbol, which may be for another function!).
  # We do have a return address and there may be a CALL instruction right before the return address that we
  # can use to find the correct symbol for the function.
  asDisassemblyBeforeReturnAddressOutput = oProcess.fasExecuteCdbCommand(
    sCommand = ".if($vvalid(0x%X, 1)) { .if (by(0x%X) == 0xe8) { .if($vvalid(0x%X, 4)) { u 0x%X L1; }; }; };" % \
        (uReturnAddress - 5, uReturnAddress - 5, uReturnAddress - 4, uReturnAddress -5),
    sComment = "Get call instruction for return address 0x%X" % uReturnAddress,
  );
  if len(asDisassemblyBeforeReturnAddressOutput) == 0:
    return None;
  if len(asDisassemblyBeforeReturnAddressOutput) == 1:
    sDissassemblyBeforeReturnAddress = asDisassemblyBeforeReturnAddressOutput[0];
  else:
    assert len(asDisassemblyBeforeReturnAddressOutput) == 2, \
        "Expected 1 or 2 lines of disassembly output, got %d:\r\n%s" % \
        (len(asDisassemblyBeforeReturnAddressOutput), "\r\n".join(asDisassemblyBeforeReturnAddressOutput));
    # first line should be cdb_module_id ["!" function_name] [ "+"/"-" "0x" offset_from_module_or_function] ":"
    assert re.match(r"^\s*\w+(?:!.+?)?(?:[\+\-]0x[0-9A-F]+)?:\s*$", asDisassemblyBeforeReturnAddressOutput[0], re.I), \
        "Unexpected disassembly output line 1:\r\n%s" % "\r\n".join(asDisassemblyBeforeReturnAddressOutput);
    sDissassemblyBeforeReturnAddress = asDisassemblyBeforeReturnAddressOutput[1];
  oDirectCallMatch = re.match(
    "^(?:%s)$" % "".join([
      r"[0-9`a-f]+",                                  # instruction_address
      r"\s+" r"e8" r"[0-9`a-f]{8}",                   # space "e8" call_offset
      r"\s+" r"call",                                 # space "call" 
      r"\s+" r"(\w+)" r"!" r"(.+?)",                  # space (cdb_module_id) "!" (function_name) 
      r"(" r"\s*" r"\+" r"\s*0x" r"[0-9`a-f]+" r")?", # [ [space] "+" [space] offset ]
      r"\s+" r"\([0-9`a-f]+\)",                       # space "(" address ")"
    ]),
    sDissassemblyBeforeReturnAddress,
    re.I,
  );
  if not oDirectCallMatch:
    return None;
  sModuleCdbId, sFunctionSymbol, sOffset = oDirectCallMatch.groups();
  if sOffset:
    # This symbol makes no sense: a call should be to the first instruction of a function and thus have no offset.
    return None;
  oModule = oProcess.foGetOrCreateModuleForCdbId(sModuleCdbId);
  oFunction = oModule.foGetOrCreateFunctionForSymbol(sFunctionSymbol);
  return (oModule, oFunction);