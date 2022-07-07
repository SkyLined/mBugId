def cProcess_fLoadSymbols(oProcess):
  oProcess.fasbExecuteCdbCommand(
    sbCommand = b".symopt+ 0x80000000",
    sb0Comment = b"Enable symbol loading debug messages",
  );
  for oModule in oProcess.doModule_by_uStartAddress.values():
    oModule.fLoadSymbols();
    oProcess.fasbExecuteCdbCommand(
      sbCommand = b"lm a 0x%X" % oModule.uStartAddress,
      sb0Comment = b"Enable symbol loading debug messages",
    );
  oProcess.fasbExecuteCdbCommand(
    sbCommand = b".symopt- 0x80000000",
    sb0Comment = b"Disable symbol loading debug messages",
  );
