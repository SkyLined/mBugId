2016-11-16
==========
API changes
-----------
+ dxBugIdConfig is now read from `dxConfig["cBugId"]` rather than
  `dxConfig["BugId"]`.
+ Failure to start an application now results in an exception. This makes more
  sense and allows you to distinguish between an application terminating after
  running, or an application not running at all.

Improvements
------------
+ cBugId now shows you which arguments it takes exactly.
+ More Edge and Firefox assertions that trigger an int3 are detected as such.
+ Charset, CSP and MSIE X-UA-Compatible data in HTML reports for better UI.
+ Twitter card info in HTML report (in case you ever link to one in a tweet).

Bug fixes
---------
+ cdb termination while generating a cBugReport could cause an exception. This
  is now handled correctly.
+ More cdb warnings that caused assertions are ignored.

2016-11-08
==========
Some of the changes can result in different BugIds for the same crash with this
version as compared to previous versions. See below for details.

API changes
-----------
+ The `bGetDetailsHTML` argument of `cBugId` was renamed to
 `bGenerateReportHTML` to better reflect what it does and for naming
 consistency across the code.
+ `cBugId` has two new arguments: `asLocalSymbolPaths` and `asSymbolCachePaths`:
  + `asLocalSymbolPaths` should be used to provide a list of folders that
    contain locally stored symbols, such as those generated when compiling a
    binary yourself.
  + `asSymbolCachePaths` should be used to provide a list of folders in which
    symbols can be downloaded from symbol servers and is used as a cache.
    This argument replaces the `asSymbolCachePaths` setting in
    `dxBugIdConfig.py`.
+ The `asDefaultSymbolCachePaths` setting was added to `dxBugIdConfig.py`.
  This value is used if no `asSymbolCachePaths` argument is provided to `cBugId`
  or if `None` is provided. If you do not want to use any symbol cache paths,
  you should use `asSymbolCachePaths = []`.
+ The `asDefaultSymbolServerURLs` setting has been added to `dxBugIdConfig.py`.
  This value is used if no `asSymbolServerURLs` argument is provided to `cBugId`
  or if `None` is provided. If you do not want to use any symbol servers, you
  should use `asSymbolServerURLs = []`.
+ The `bMakeSureSymbolsAreLoaded` setting has been added to control whether
  symbols load errors are detected and fixed. It is disabled by default, which
  is a break from the original behavior, because this can significantly speed
  up analysis. If you are experiencing problems generating consistent reports
  and are missing symbols, you may want to re-enable this setting to see if this
  fixes the issue for you.

Improvements
------------
+ Analysis should be much faster: getting the values of register and pseudo
  registers was done in a way that triggered a symbol look-up, which is very
  slow (10 seconds or more). this is now done in a different way that avoids
  this, which should greatly improve analysis speed in many cases.
+ Detect more Control Flow Guard breakpoint exceptions.
+ The interval for CPU usage tests has been decreased to speed up these tests.

Bug fixes
---------
+ With HTML reports disabled, code that creates part of the HTML report would
  still execute while getting the stack. This code could then cause an
  exception. This code is no longer executed if not HTML report is required.
+ With HTML reports disabled, code that creates part of the HTML report for
  binary module information would still be executed. This code is no longer
  executed if not HTML report is required.
+ The code handling VERIFIER STOPs would assume page heap information would
  always be available and contain the memory block address and size, which is
  not the case (e.g. the block start address and size is not available for
  freed memory blocks. This could cause an exception. The code now handles this
  correctly.
+ Bug translation could fail if a stack frame had no symbol. This could result
  in bug being translated incorrectly, and getting the wrong type (e.g. an
  Assert could be reported as an OOM). This has been fixed.
+ Stack hashed and the crash location were not ideal when a relevant stack
  frame had no symbols. This has been fixed.

2016-10-13
==========
Breaking changes
----------------
+ Renamed sDetailsHTML property of bug report to sReportHTML (and
  sDetailsHTMLTemplate to sReportHTMLTemplate).
+ Don't count stack frames without a symbol towards the number of hashed frames.
  They are added to the hash as a placeholder (`-`), so you hash may get larger
  than what you could previously expect.

Improvements
------------
+ Replace tabs with spaces where appropriate in HTML report.
+ Add ISA to module version information.
+ Handle STATUS_WAKE_SYSTEM_DEBUGGER better.


2016-10-12
==========
Improvements
------------
+ Cleanup stack for VERIFIER STOP message by removing top stack frames that are
  irrelevant, as is already done for other bugs.


2016-10-11
==========
Bug fixes
---------
+ Add missing include in code handling unexpected cdb termination.
+ Add missing property to report for unexpected cdb termination.
+ Disable automatically applying of page heap: it was causing access violations
  for unknown reasons.


2016-10-10
==========
New features
------------
+ Page heap settings are now automatically applied by default to all processes
  to ensure best results. Settings can be used to disable this if needed. Which
  settings are applied can also be modified through settings.

Bugfixes
--------
+ cCdbWrapper_fuGetValue now ignores an additional cdb warning.


2016-10-07
==========
New or changed BugIds
---------------------
+ Detect and report misaligned frees in VERIFIER STOP heap stamp corruptions,
  the BugId takes the for `MisalignedFree[size]+offset`. e.g if the code
  attempts to free heap using a pointer that is at offset 0x8 of a 0x20 byte
  block, you will get a BugId of `MisalignedFree[0x20]+8`
+ The `FailFast2:` prefix was removed from FailFast exceptions.
+ Both `LegacyGS` and `StackCookie` FailFast exceptions are now reported as
  `OOBW[Stack]` (as in: Out-Of-Bounds Write on the Stack).

Improvements
------------
+ Mayor rewrite of page heap information handling, same code now used when an
  access violation is handled as well as for VERIFIER STOPs.
+ Rewrite of parts of the VERIFIER STOP handling code.
+ Change code to not generate information for the HTML report when this is not
  needed.
+ memory dumps in HTML reports contain more information.
+ Rewrote parts of the memory corruption detector.


2016-10-05
==========
Bug fixes and improvements
--------------------------
+ Handle error output by cdb when getting value using cCdbWrapper.fuGetValue.
+ Fix typo in new FailFast code that caused exception when dumping stack.


2016-10-04
==========
New features
------------
+ Add stack dump to FailFast exceptions that report stack cookie corruption.
+ Add VERIFIER STOP message to reports.

Bug fixes and improvements
--------------------------
+ New way of dumping memory regions and marking memory addresses and ranges
  with remarks.
+ Some layout changes in memory regions in HTML reports.
+ Improve sanity checks in code that detects VERIFIER STOP messages.
+ Rewrote parts of CPU usage detection code.


2016-09-13
==========
Alterations to bug report
-------------------------
+ Default security impact is no longer None but "Denial of Service".

Bug fixes and improvements
--------------------------
+ Reorder HTML report output and add source.
+ Fix bug where binary version information was not available when HTML report
  was not generated.


2016-09-12
==========
New features
------------
+ Output application command-line in HTML report.

Alterations to exception handling
---------------------------------
+ Ignore first chance STATUS_HANDLE_NOT_CLOSABLE exceptions, similar to how
  other handle related exceptions are handled.

Bug fixes and improvements
--------------------------
+ Avoids problems in timezone parsing in debugger time.
+ Make stack handling more robust.


2016-09-09
==========
Added features
--------------
+ Added `cBugReport.asVersionInformation`, which contains version information
  on the main process binary (i.e. the .exe) and the binary in which the crash
  happened if it's not the main process binary (i.e. a .dll).


2016-09-08
==========
Bug fixes and improvements
--------------------------
+ Avoid some exceptions that can happen after cdb has terminated, when the code
  tries to make sure it has.
+ Report descriptive error if FileSystem or Kill are not found.
+ Handle empty arguments to the application ("")


2016-09-07
==========
Alterations to BugIds
---------------------
+ Replace "?" in BugIds with "_": this improvies legibility
  IMHO and makes use of the BugId in a file or folder name easier.

Bug fixes and improvements
--------------------------
+ Handle negative offsets in time zone in debugger time to prevent an exception.
+ Add another Chrome OOM crash signature
+ Improve handling of symbol problems in page heap output.


2016-09-05
==========
+ Bug fixes, no API changes.


2016-08-31
==========
Alterations to BugIds
---------------------
+ The BugId can now include the number of overwritten bytes, and a hash of
  their values if you supply a dxBugIdConfig["uHeapCorruptedBytesHashChars"]
  setting value of 1 or more. This can be useful when you want to detect if
  two instances of heap corruption wrote the same data to corrupt the heap.
  When enabled, a string with format "~L:H" is added to the BugId, where "L" is
  the length of the corruption and "H" is the hash. Note that L is not
  influenced by dxBugIdConfig["uArchitectureIndependentBugIdBits"], so BugId's
  created using this feature on x86 and x64 versions of an application may
  differ.

API changes
-----------
+ cCdbWrapper has a new first argument "sCdbISA" inserted before the existing
  arguments. This argument indicates which version of cdb to use (x86 or x64,
  default depends on the OS ISA). Using the x86 cdb to debug x86 applications
  can improve the accuracy of results over using the x64 cdb, as the later may
  not load the right symbols for ntdll, which prevents BugId from collecting
  page heap information.
+ Added dxBugIdConfig["uHeapCorruptedBytesHashChars"] (see above).

Bug fixes and improvements
--------------------------
+ Better handling of some OOM cases
+ Better handling of failure to match symbol to address while generating
  assembly HTML
+ Better handling of some STATUS_STACK_BUFFER_OVERRUN cases
+ Show values of overwritten bytes in cases where heap corruption occurs.
+ cStackFrame objects now have an oPreviousFrame property, which is set to the
  frame that is lower in number (i.e. the frame that was called from this
  frame).
+ The sCdbISA argument to cCdbWrapper makes it easier to run x86 tests on x64
  OS-es, so these have been re-enabled.
+ FastFail:AppExit was not reported as a potential security issue, but since
  it can be triggered by a R6025 pure virtual function call, it can be and the
  description now reflects this.
+ The code could make excessive calls to fApplicationRunningCallback, this has
  been fixed.