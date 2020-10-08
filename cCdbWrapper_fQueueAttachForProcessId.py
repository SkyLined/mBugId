def cCdbWrapper_fQueueAttachForProcessId(oCdbWrapper, uProcessId):
  assert oCdbWrapper.oCdbConsoleProcess is not None, \
      "You cannot attach to a process when cdb is not running."
  # Queue the process id for attaching when the application is paused and cdb is
  # accepting commands (it might accept commands now, but it's easier to always
  # queue and have the main cdb std I/O loop handle executing the attach
  # commands).
  oCdbWrapper.auProcessIdsPendingAttach.append(uProcessId);
  oCdbWrapper.fInterrupt(
    "Attaching to process %d/0x%X" % (uProcessId, uProcessId),
  );
