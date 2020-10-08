def cCdbWrapper_fUpdateCdbISA(oCdbWrapper):
  if oCdbWrapper.oCdbCurrentProcess.sISA != oCdbWrapper.sCdbCurrentISA:
    # Select process ISA if it is not yet the current ISA. ".block{}" is required
    oCdbWrapper.fasExecuteCdbCommand(
      sCommand = ".effmach %s;" % {"x86": "x86", "x64": "amd64"}[oCdbWrapper.oCdbCurrentProcess.sISA],
      sComment = "Switch to current process ISA",
      bRetryOnTruncatedOutput = True,
    );
    # Assuming there's no error, track the new current isa.
    oCdbWrapper.sCdbCurrentISA = oCdbWrapper.oCdbCurrentProcess.sISA;
