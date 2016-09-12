2016-09-12
==========
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