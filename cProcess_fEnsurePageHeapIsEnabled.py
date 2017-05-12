import re;

# Cache which binaries have page heap enabled/disabled. this assumes that the user does not modify the page heap
# settings while BugId is running.
gdbPageHeapEnabled_by_sBinaryName = {};

def cProcess_fEnsurePageHeapIsEnabled(oProcess):
  oCdbWrapper = oProcess.oCdbWrapper;
  if oProcess.bPageHeapEnabled is not None:
    return; # We have ensured this before.
  if oProcess.sBinaryName in gdbPageHeapEnabled_by_sBinaryName:
    oProcess.bPageHeapEnabled = gdbPageHeapEnabled_by_sBinaryName[oProcess.sBinaryName];
    return;
  oProcess.fSelectInCdb();
  asPageHeapStatusOutput = oCdbWrapper.fasSendCommandAndReadOutput("!heap -p; $$ Get page heap status");
  #### Page heap disabled ####################################################
  # |    Active GlobalFlag bits:
  # |        htc - Enable heap tail checking
  # |        hfc - Enable heap free checking
  # |        hpc - Enable heap parameter checking
  # |    active heaps:
  # |
  # | - 2cb0000
  # |          HEAP_GROWABLE HEAP_TAIL_CHECKING_ENABLED HEAP_FREE_CHECKING_ENABLED 
  # | - 2f40000
  # |          HEAP_GROWABLE HEAP_TAIL_CHECKING_ENABLED HEAP_FREE_CHECKING_ENABLED HEAP_CLASS_1 
  #### Page heap enabled #####################################################
  # |    Active GlobalFlag bits:
  # |        scb - Enable system critical breaks
  # |        hpa - Place heap allocations at ends of pages
  # |
  # |    StackTraceDataBase @ 04500000 of size 01000000 with 00000013 traces
  # |
  # |    PageHeap enabled with options:
  # |        ENABLE_PAGE_HEAP
  # |        COLLECT_STACK_TRACES
  # |
  # |    active heaps:
  # |
  # |    + 4370000
  # |        ENABLE_PAGE_HEAP COLLECT_STACK_TRACES 
  # |      NormalHeap - 5690000
  # |          HEAP_GROWABLE 
  # |    + 5500000
  # |        ENABLE_PAGE_HEAP COLLECT_STACK_TRACES 
  # |      NormalHeap - 5850000
  # |          HEAP_GROWABLE HEAP_CLASS_1
  ############################################################################
  # It turns out that when a new process is created, the !heap command may be unable to provide us the information we
  # need. This is probably because the process was just created and is still being initialized, so insufficient data
  # is available at this point. I work around this by repeatedly calling this function, so we can try again and again
  # until it works.
  # Find the "Active GlobalFlag bits:"-header
  for uPageHeapOptionsIndex in xrange(len(asPageHeapStatusOutput)):
    if asPageHeapStatusOutput[uPageHeapOptionsIndex].strip() == "Active GlobalFlag bits:":
      break;
  else:
    # The header was not found, try again later:
    return;
  asRequiredOptions = ["ENABLE_PAGE_HEAP", "COLLECT_STACK_TRACES"];
  # Find the "PageHeap enabled with options:"-header and see if the required options come after it:
  while uPageHeapOptionsIndex < len(asPageHeapStatusOutput):
    bHeaderFound = asPageHeapStatusOutput[uPageHeapOptionsIndex].strip() == "PageHeap enabled with options:";
    uPageHeapOptionsIndex += 1;
    if bHeaderFound:
      # Check the which options are reported after the header:
      asEnabledOptions = [];
      while uPageHeapOptionsIndex < len(asPageHeapStatusOutput):
        sEnabledOption = asPageHeapStatusOutput[uPageHeapOptionsIndex].strip();
        if not sEnabledOption:
          # An empty line follow the options.
          break;
        if sEnabledOption in asRequiredOptions:
          # Mark the required option as enabled
          asEnabledOptions.append(sEnabledOption);
        uPageHeapOptionsIndex += 1;
      # See which required options are not enabled:
      asMissingOptions = [s for s in asRequiredOptions if s not in asEnabledOptions];
      if not asMissingOptions:
        # Page heap is enabled correctly.
        gdbPageHeapEnabled_by_sBinaryName[oProcess.sBinaryName] = True;
        oProcess.bPageHeapEnabled = True;
        return;
      break;
  # Page heap is not enabled or not all the required options are enabled
  oProcess.bPageHeapEnabled = False;
  # The "id" cdb uses to identify modules in symbols is normally based on the name of the module binary file.
  # However, for unknown reasons, cdb will sometimes use "imageXXXXXXXX", where XXXXXXXX is the hex address at
  # which the module is loaded (this has only been seen on x86 so far). In such cases, page heap appears to be
  # disabled; I believe whatever keeps cdb from determining the module binary's file name is also keeping page heap
  # from doing the same. In such cases, it appears that page heap cannot be enabled by the user, so we'll report it
  # with the second argument as "False" (not preventable).
  bPreventable = re.match(r"image[0-9a-f]{8}", oProcess.oMainModule.sCdbId, re.I) is None;
#  print "@@@ Page heap status is %s DISABLED for %s" % (bPreventable and "PREVENTABLY" or "PERMANENTLY", oProcess.sBinaryName);
  # Report it
  oCdbWrapper.fPageHeapNotEnabledCallback(oProcess.uId, oProcess.sBinaryName, bPreventable);
