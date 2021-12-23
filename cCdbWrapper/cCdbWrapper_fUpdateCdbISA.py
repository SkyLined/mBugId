def cCdbWrapper_fUpdateCdbISA(oCdbWrapper):
  if oCdbWrapper.oCdbCurrentProcess.sISA != oCdbWrapper.sCdbCurrentISA:
    # Select process ISA if it is not yet the current ISA. ".block{}" is required
    oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = b".effmach %s;" % {"x86": b"x86", "x64": b"amd64"}[oCdbWrapper.oCdbCurrentProcess.sISA],
      sb0Comment = b"Switch to current process ISA",
      bRetryOnTruncatedOutput = True,
    );
    # Assuming there's no error, track the new current isa.
    oCdbWrapper.sCdbCurrentISA = oCdbWrapper.oCdbCurrentProcess.sISA;
