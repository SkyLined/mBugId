def cCdbWrapper_fEnsurePageHeapIsEnabledInCurrentProcess(oCdbWrapper):
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
    
    # Find the "PageHeap enabled with options:"-header
    for uPageHeapOptionsIndex in xrange(len(asPageHeapStatusOutput)):
      if asPageHeapStatusOutput[uPageHeapOptionsIndex].strip() == "PageHeap enabled with options:":
        break;
    else:
      # Not found: page heap is not enabled. Either throw an exception or call the callback.
      oCdbWrapper.fPageHeapNotEnabledCallback("Page heap not enabled for %s" % oCdbWrapper.oCurrentProcess.sBinaryName);
      return;
    # Extract which flags are enabled and see if all required flags are:
    uPageHeapOptionsIndex += 1;
    asRequiredOptions = ["ENABLE_PAGE_HEAP", "COLLECT_STACK_TRACES"];
    while uPageHeapOptionsIndex < len(asPageHeapStatusOutput):
      sEnabledOption = asPageHeapStatusOutput[uPageHeapOptionsIndex].strip();
      if not sEnabledOption:
        break;
      if sEnabledOption in asRequiredOptions:
        asRequiredOptions.remove(sEnabledOption);
      uPageHeapOptionsIndex += 1;
    if asRequiredOptions:
      if len(asRequiredOptions) == 1:
        sError = "Page heap flag %s is not enabled for %s" % \
            (asRequiredOptions[0], oCdbWrapper.oCurrentProcess.sBinaryName);
      else:
        sError = "Pahe heap flags %s and %s are not enabled for %s" % \
            (", ".join(asRequiredOptions[:-1]), asRequiredOptions[-1], oCdbWrapper.oCurrentProcess.sBinaryName);
      oCdbWrapper.fPageHeapNotEnabledCallback(sError);
