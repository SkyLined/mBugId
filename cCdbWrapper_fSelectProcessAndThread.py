def cCdbWrapper_fSelectProcessAndThread(oCdbWrapper, uProcessId = None, uThreadId = None):
  # Both arguments are optional
  sSelectCommand = "";
  asSelected = [];
  if uProcessId is not None and (oCdbWrapper.oCdbCurrentProcess is None or uProcessId != oCdbWrapper.oCdbCurrentProcess.uId):
    # Select process if it is not yet the current process.
    assert uProcessId in oCdbWrapper.doProcess_by_uId, \
        "Unknown process id %d/0x%X" % (uProcessId, uProcessId);
    sSelectCommand += "|~[0x%X]s;" % uProcessId;
    asSelected.append("process");
    # Assuming there's no error, track the new current process.
    oCdbWrapper.oCdbCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
    if oCdbWrapper.oCdbCurrentProcess.sISA != oCdbWrapper.sCdbCurrentISA:
      # Select process ISA if it is not yet the current ISA. ".block{}" is required
      sSelectCommand += ".block{.effmach %s;};" % {"x86": "x86", "x64": "amd64"}[oCdbWrapper.oCdbCurrentProcess.sISA];
      # Assuming there's no error, track the new current isa.
      oCdbWrapper.sCdbCurrentISA = oCdbWrapper.oCdbCurrentProcess.sISA;
      asSelected.append("isa");
  if uThreadId is not None:
    # We're not tracking the current thread; always set this.
    # TODO: track the current thread to reduce the number of times we may need to execute this command:
    sSelectCommand += "~~[0x%X]s;" % uThreadId;
    oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
    asSelected.append("thread");
  if sSelectCommand:
    # We need to select a different process, isa or thread in cdb.
    asSelectCommandOutput = oCdbWrapper.fasExecuteCdbCommand(
      sCommand = sSelectCommand,
      sComment = "Select %s" % "/".join(asSelected),
    );
    # cdb may or may not output the last instruction :S. But it will always output the isa on the last line if selected.
    if "isa" in asSelected:
      bUnexpectedOutput = asSelectCommandOutput[-1] not in [
        "Effective machine: x86 compatible (x86)",
        "Effective machine: x64 (AMD64)"
      ];
    else:
      bUnexpectedOutput = False; #len(asSelectCommandOutput) != 0;
    assert not bUnexpectedOutput, \
        "Unexpected select %s output:\r\n%s" % ("/".join(asSelected), "\r\n".join(asSelectCommandOutput));
    if "process" in asSelected and "thread" not in asSelected:
      # We changed the process, but did not choose a thread; find out what the new thread is:
      uThreadId = oCdbWrapper.fuGetValueForRegister("$tid", "Get current thread id");
      oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
