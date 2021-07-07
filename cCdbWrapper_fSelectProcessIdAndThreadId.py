def cCdbWrapper_fSelectProcessIdAndThreadId(oCdbWrapper, uProcessId = None, uThreadId = None):
  # Both arguments are optional
  sbSelectCommand = b"";
  asbSelected = [];
  if uProcessId is not None and (oCdbWrapper.oCdbCurrentProcess is None or uProcessId != oCdbWrapper.oCdbCurrentProcess.uId):
    # Select process if it is not yet the current process.
    assert uProcessId in oCdbWrapper.doProcess_by_uId, \
        "Unknown process id %d/0x%X" % (uProcessId, uProcessId);
    sbSelectCommand += b"|~[0x%X]s;" % uProcessId;
    asbSelected.append(b"process");
    # Assuming there's no error, track the new current process.
    oCdbWrapper.oCdbCurrentProcess = oCdbWrapper.doProcess_by_uId[uProcessId];
    if oCdbWrapper.oCdbCurrentProcess.sISA != oCdbWrapper.sCdbCurrentISA:
      # Select process ISA if it is not yet the current ISA. ".block{}" is required
      sbSelectCommand += b".block{.effmach %s;};" % {"x86": b"x86", "x64": b"amd64"}[oCdbWrapper.oCdbCurrentProcess.sISA];
      # Assuming there's no error, track the new current isa.
      oCdbWrapper.sCdbCurrentISA = oCdbWrapper.oCdbCurrentProcess.sISA;
      asbSelected.append(b"isa");
  if uThreadId is not None:
    # We're not tracking the current thread; always set this.
    # TODO: track the current thread to reduce the number of times we may need to execute this command:
    sbSelectCommand += b"~~[0x%X]s;" % uThreadId;
    oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
    asbSelected.append(b"thread");
  if sbSelectCommand:
    # We need to select a different process, isa or thread in cdb.
    asbSelectCommandOutput = oCdbWrapper.fasbExecuteCdbCommand(
      sbCommand = sbSelectCommand,
      sb0Comment = b"Select %s" % b"/".join(asbSelected),
    );
    # cdb may or may not output the last instruction :S. But it will always output the isa on the last line if selected.
    if b"isa" in asbSelected:
      bUnexpectedOutput = asbSelectCommandOutput[-1] not in [
        b"Effective machine: x86 compatible (x86)",
        b"Effective machine: x64 (AMD64)"
      ];
    else:
      bUnexpectedOutput = False; #len(asbSelectCommandOutput) != 0;
    assert not bUnexpectedOutput, \
        "Unexpected select %s output:\r\n%s" % (b"/".join(asbSelected), b"\r\n".join(asbSelectCommandOutput));
    if b"process" in asbSelected and b"thread" not in asbSelected:
      # We changed the process, but did not choose a thread; find out what the new thread is:
      uThreadId = oCdbWrapper.fuGetValueForRegister(b"$tid", b"Get current thread id");
      oCdbWrapper.oCdbCurrentWindowsAPIThread = oCdbWrapper.oCdbCurrentProcess.foGetWindowsAPIThreadForId(uThreadId);
