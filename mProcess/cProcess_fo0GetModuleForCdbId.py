
gbDebugOutput = False;

def cProcess_fo0GetModuleForCdbId(oProcess, sbCdbId):
  # First check if we have cached this cdb id:
  for oModule in oProcess.doModule_by_uStartAddress.values():
    if oModule.fbIsCdbIdCached() and oModule.sbCdbId == sbCdbId:
      return oModule;
  # TODO remove this once issue 131 is fixed.
  # https://github.com/SkyLined/BugId/issues/131
  asbLoadedModulesInCdbForDebugging = oProcess.fasbExecuteCdbCommand(
    b"lm;",
    b"Get list of loaded modules for debugging"
  );
  asLoadedModulesByStartAddressForDebugging = [
    "%s: %s (%s)" % (
      oModule.uStartAddress,
      oModule.s0BinaryName or "<name unknown>",
      oModule.s0BinaryPath or "<path unknown>",
    )
    for oModule in oProcess.doModule_by_uStartAddress.values()
  ];
  # No; try to find the start address of the module for this cdb id:
  u0StartAddress = oProcess.fu0GetAddressForSymbol(sbCdbId);
  assert u0StartAddress is not None, \
    "cdb does not appear to know the address for module symbol '%s'!?" % sbCdbId;
  uStartAddress = u0StartAddress;
  # No; try to get the module for the start address:
  o0Module = oProcess.fo0GetModuleForStartAddress(uStartAddress);
  assert o0Module is not None, \
      "cdb reports module '%s' to be at address 0x%x but there is no module there!?" % (
        sbCdbId,
        uStartAddress
      );
  oModule = o0Module;
  if gbDebugOutput:
    print("cdb id %s (address %s) => %s" % (
      repr(sbCdbId)[1:],
      fsHexNumber(uStartAddress),
      oModule,
    ));
  
  if oModule.sbCdbId != sbCdbId:
    # cdb ids may have aliases because life isn't hard enough without them.
    u0ModuleSymbolStartAddress = oProcess.fu0GetAddressForSymbol(oModule.sbCdbId);
    assert uStartAddress == u0ModuleSymbolStartAddress, \
        "got unexpected module cdb id and address: requested %s=>%s, got %s=>%s (module at %s)" % (
          repr(sbCdbId)[1:],
          fsHexNumber(uStartAddress),
          oModule.sbCdbId,
          fsHexNumber(u0ModuleSymbolStartAddress) if u0ModuleSymbolStartAddress is not None else "<no address>",
          fsHexNumber(oModule.uStartAddress),
        );
    # Change the cdb id of the module to the one we were using already:
    oModule.sbCdbId = sbCdbId;
  return oModule;
