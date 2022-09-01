def cProcess_fLoadSymbols(oSelf):
  # Running this more than once would make no sense.
  if oSelf.oCdbWrapper.bDoNotLoadSymbols:
    return;
  if oSelf.bSymbolsLoaded:
    return;
  oSelf.fasbExecuteCdbCommand(
    sbCommand = b".symopt+ 0x80000000",
    sb0Comment = b"Enable symbol loading debug messages",
  );
  for oModule in oSelf.doModule_by_uStartAddress.values():
    oModule.fLoadSymbols();
    oSelf.fasbExecuteCdbCommand(
      sbCommand = b"lm a 0x%X" % oModule.uStartAddress,
      sb0Comment = b"Enable symbol loading debug messages",
    );
  oSelf.fasbExecuteCdbCommand(
    sbCommand = b".symopt- 0x80000000",
    sb0Comment = b"Disable symbol loading debug messages",
  );
  oSelf.bSymbolsLoaded = True;
