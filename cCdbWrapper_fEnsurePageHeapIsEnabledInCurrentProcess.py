import re;

def cCdbWrapper_fEnsurePageHeapIsEnabledInCurrentProcess(oCdbWrapper):
  if oCdbWrapper.oCurrentProcess.sBinaryName in oCdbWrapper.asBinaryNamesWithPageHeapEnabled:
    return;
  if re.match(r"image[0-9a-f]{8}", oCdbWrapper.oCurrentProcess.oMainModule.sCdbId, re.I):
    # The "id" cdb uses to identify modules in symbols is normally based on the name of the module binary file.
    # However, for unknown reasons, cdb will sometimes use "imageXXXXXXXX", where XXXXXXXX is the hex address at
    # which the module is loaded (this has only been seen on x86 so far). In such cases, page heap appears to be
    # disabled; I believe whatever keeps cdb from determining the module binary's file name is also keeping page heap
    # from doing the same. In such cases, it appears that page heap cannot be enabled by the user, so we'll report it
    # with the second argument as "False" (not preventable).
    oCdbWrapper.fPageHeapNotEnabledCallback(oCdbWrapper.oCurrentProcess.uId, oCdbWrapper.oCurrentProcess.sBinaryName, False);
    return;
  asPageHeapStatusOutput = oCdbWrapper.fasSendCommandAndReadOutput("!heap -p; $$ Get page heap status");
  #### Page heap disabled ####################################################
  #    Active GlobalFlag bits:
  #        htc - Enable heap tail checking
  #        hfc - Enable heap free checking
  #        hpc - Enable heap parameter checking
  #    active heaps:
  #
  # - 2cb0000
  #          HEAP_GROWABLE HEAP_TAIL_CHECKING_ENABLED HEAP_FREE_CHECKING_ENABLED 
  # - 2f40000
  #          HEAP_GROWABLE HEAP_TAIL_CHECKING_ENABLED HEAP_FREE_CHECKING_ENABLED HEAP_CLASS_1 
  #### Page heap enabled #####################################################
  #    Active GlobalFlag bits:
  #        scb - Enable system critical breaks
  #        hpa - Place heap allocations at ends of pages
  #
  #    StackTraceDataBase @ 04500000 of size 01000000 with 00000013 traces
  #
  #    PageHeap enabled with options:
  #        ENABLE_PAGE_HEAP
  #        COLLECT_STACK_TRACES
  #
  #    active heaps:
  #
  #    + 4370000
  #        ENABLE_PAGE_HEAP COLLECT_STACK_TRACES 
  #      NormalHeap - 5690000
  #          HEAP_GROWABLE 
  #    + 5500000
  #        ENABLE_PAGE_HEAP COLLECT_STACK_TRACES 
  #      NormalHeap - 5850000
  #          HEAP_GROWABLE HEAP_CLASS_1
  ############################################################################
  asValidOptions = ["ENABLE_PAGE_HEAP", "COLLECT_STACK_TRACES"];
  # Find the "PageHeap enabled with options:"-header
  for uPageHeapOptionsIndex in xrange(len(asPageHeapStatusOutput)):
    if asPageHeapStatusOutput[uPageHeapOptionsIndex].strip() == "PageHeap enabled with options:":
      # Extract which flags are enabled and see if all required flags are:
      uPageHeapOptionsIndex += 1;
      asEnabledOptions = [];
      while uPageHeapOptionsIndex < len(asPageHeapStatusOutput):
        sEnabledOption = asPageHeapStatusOutput[uPageHeapOptionsIndex].strip();
        if not sEnabledOption:
          break;
        if sEnabledOption in asValidOptions:
          asEnabledOptions.append(sEnabledOption);
        uPageHeapOptionsIndex += 1;
      asMissingOptions = [s for s in asValidOptions if s not in asEnabledOptions];
      if not asMissingOptions:
        oCdbWrapper.asBinaryNamesWithPageHeapEnabled.append(oCdbWrapper.oCurrentProcess.sBinaryName);
        return;
      break;
  # This is preventable by the user: report it as preventable.
  oCdbWrapper.fPageHeapNotEnabledCallback(oCdbWrapper.oCurrentProcess.uId, oCdbWrapper.oCurrentProcess.sBinaryName, True);
