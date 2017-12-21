from dsDebuggingToolsPath_sISA import dsDebuggingToolsPath_sISA;

uKiloByte = 10 ** 3;
uMegaByte = 10 ** 6;
uGigaByte = 10 ** 9;
uTeraByte = 10 ** 12;

# Add default values where no values have been supplied:
dxConfig = {
  ### cdb/kill binary settings
  "sDebuggingToolsPath_x86": dsDebuggingToolsPath_sISA.get("x86"),
  "sDebuggingToolsPath_x64": dsDebuggingToolsPath_sISA.get("x64"),
  ### Pointer settings
  "uMaxAddressOffset": 0x1000,          # How big an offset from a special address (such as NULL) do you expect in your
                                        # application? Anything within this range from a special address is considered
                                        # to be a pointer to that address + an offset.
  "uArchitectureIndependentBugIdBits": 0, # 0 to disable or 8, 6, 32, ... to enable architecture agnostic sizes
                                        # and offsets in BugIds. For X > 0, and Y = X/8, the bug id will show numbers
                                        # that are larger than Y as "Yn+R", where R is the remainder of the number
                                        # modulo Y.
                                        # For example: when testing both 32-bit and 64-bit versions of an application,
                                        # you may get different bug ids for the same access violation bug, because the
                                        # sizes and offsets depends on the architecture. However, if you set this value
                                        # to 32 (X = 32, Y = 4), the uniqueness of the offsets and sizes is reduced to
                                        # the point where you should get the same bug ids:
                                        #  0,  1,  2,  3      => "0", "1", "2", "3",
                                        #  4,  8, 12, 16, ... => "4n"
                                        #  5,  9, 13, 17, ... => "4n+1"
                                        #  6, 10, 14, 18, ... => "4n+2"
                                        #  7, 11, 15, 19, ... => "4n+3"
  "uHeapCorruptedBytesHashChars": 4,    # Put a hash of the values of modified bytes in the id. Can be useful when
                                        # attempting to modify some input that triggers the heap corruption in order to
                                        # find out if this affects the corruption: if this ends up modifying the values
                                        # that are written to the heap, the BugId will change with it. It may also
                                        # result in many different BugIds for the same bug if the bytes written depend
                                        # on things not in the input that triggered the bug, e.g. timing.
  "uMaxExportFunctionOffset": 0x30,     # When using export symbols, anything but a direct hit is not reliable; the
                                        # higher an offset gets, the less reliable it is. You can choose the cut off
                                        # point using this option: any offset up to and including this number is
                                        # considered to be valid, any larger offset is not considerd valid and will
                                        # be converted into module + offset instead.
  ### Stack hash settings
  "uStackHashFramesCount": 2,           # How many stack frames are hashed for the crash id?
  "uMaxStackFrameHashChars": 3,         # How many characters of hash to use in the id for each stack frame.
  ### HTML Report Disassembly settings
  "uDisassemblyInstructionsBefore": 0x40, # How many instructions to disassemble before the current instruction or the
                                        # return address of the stack frame.
  "uDisassemblyInstructionsAfter": 0x20, # How many instructions to disassemble after the current instruction or the
                                        # return address of the stack frame.
  "uDisassemblyAlignmentBytes": 10,     # How many instructions to start disassembling before an address in order to
                                        # make sure we don't start diassembling in the middle of the instruction that
                                        # at that address.
  "uDisassemblyAverageInstructionSize": 4, # Use to guess how many bytes to disassemble to get the requested number of
                                        # instructions
                                        # Note: BugId disassembles A * B + C bytes before and after the instruction
                                        # that triggered the crash, where A is the number of instructions requested, B
                                        # is the average instruction size provided, and C is the number of alignment
                                        # bytes (only used for the "before" instructions, it's 0 for "after"). If
                                        # uDisassemblyAlignmentBytes is too small, the first instruction you see may
                                        # not be an instruction that will ever get executed, as disassembly happed in
                                        # the middle of the "real" instruction. If uDisassemblyAverageInstructionSize
                                        # is too small, you may see less instructions than requested when not enough
                                        # bytes get disassembled to get the requested number of instructions. If the
                                        # total number of bytes disassembled is too large, you may get no disassembly
                                        # at all when part of the memory it attempts to disassemble is not readable.
  ### HTML Report Memory dump settings
  "uStackDumpSizeInPointers": 0x100,    # How many pointer sized values should a stack dump contain?
  "uMaxMemoryDumpSize": 0x1000,         # How many bytes should a memory dump contain at most? This value should be set
                                        # so the dump includes as much relevant information as possible, but not so
                                        # large that it causes a "Range error" in cdb. e.g. attempting to dump 0x6034C
                                        # pointers will fail. I've set a reasonable default, feel free to experiment.
  ### HTML Report Stack settings
  "uMaxStackFramesCount": 100,          # How many stack frames are retreived for analysis?
  "uMinStackRecursionLoops": 3,         # How many recursive functions call loops are needed to assume a stack overflow
                                        # is caused by such a loop?
  "uMaxStackRecursionLoopSize": 100,    # The maximum number of functions expected to be in a loop (less increases
                                        # analysis speed, but might miss-analyze a recursion loop involving many
                                        # functions as a simple stack exhaustion). I've seen 43 functions in one loop.
  ### Symbol loading settings
  "bDeleteCorruptSymbols": True,        # Allow BugId to try to delete symbol files that cdb claims are corrupted (but
                                        # only if a symbol server URL is provided). This may allow BugId to re-download
                                        # files.
  "uMaxSymbolLoadingRetries": 1,        # Allow BugId to reload modules in order to attempt to re-download
                                        # in symbol loading caused by corrupted pdb files. This turns on "noisy symbol
                                        # loading" which may provide useful information to fix symbol loading errors.
                                        # It has a large impact on performance, so you may want to disable it by setting
                                        # it to 0 if you can guarantee correct symbol files are available and do not
                                        # need to be downloaded (which I think is what sometimes causes this
                                        # corruption).
                                        # If you often see "CDB failed to load symbols" assertion errors, try
                                        # increasing the number and see if that resolves it.
  "asDefaultSymbolCachePaths": [""],    # Where should symbols be cached if no cache paths are provided? The default
                                        # ([""]) tells cdb to use its own default path.
  "asDefaultSymbolServerURLs": [        # What symbol servers should be used if no symbol servers are provided?
    "http://msdl.microsoft.com/download/symbols" # The default (["http://msdl.microsoft.com/download/symbols"]) tells
  ],                                    # cdb to use only the Microsoft symbol server.
  "bDeferredSymbolLoads": True,         # True means enable SYMOPT_DEFERRED_LOADS in cdb, see Debugger help for details.
  "bUse_NT_SYMBOL_PATH": True,          # Set to True to have BugId use _NT_SYMBOL_PATH for symbol caches and servers.
                                        # Set to False to have BugId ignore it and only use values from dxConfig
                                        # and the arguments provided to cBugId.
  ### Source code settings
  "bEnableSourceCodeSupport": True,     # Tell cdb to load source line symbols or not.
  "dsURLTemplate_by_srSourceFilePath": {}, # Used to translate source file paths to links to online code repository.
  ### Dump file settings
  "bSaveDump": False,                   # Save a dump file.
  "bOverwriteDump": False,              # Overwrite any existing dump file.
  "sDumpPath": None,                    # Path where you want cBugId to save dump file. None = current folder.
  "bFullDump": False,                   # Create a full (True) or small memory dump (False).
  ### Excessive CPU usage detection
  "nExcessiveCPUUsageCheckInterval": 10.0, # How many seconds to gather thread CPU usage data.
  "nExcessiveCPUUsagePercent": 90,      # How long do all threads in all processes for the application need to use the
                                        # CPU during the usage check interval to trigger an excessive CPU usage bug
                                        # report. Value in percent of the check interval, e.g. a value of 75 for a
                                        # check interval of 10s means a bug will be reported if the application uses
                                        # the CPU more than 7.5 seconds during a 10s interval.
  "nExcessiveCPUUsageWormRunTime": 1,   # How many seconds to allow a function to run to find the topmost function
                                        # involved in the CPU usage? Lower values yield results quicker, but may be
                                        # inaccurate. Higher values increase the time in which the code can run and
                                        # return to the topmost function. If you provide too large a value the CPU
                                        # using loop may finish, giving you invalid results.
  ### Timeouts
  "nTimeoutGranularity": 0.01,          # How often to check for timeouts, in seconds. Making this value smaller causes
                                        # the timeouts to fire closer to the intended time, but slows down debugging.
                                        # Making the value larger can cause timeouts to fire a lot later than requested.
  ### Exception handling
  "bIgnoreCPPExceptions": False,        # Can be used to ignore C++ exceptions completely in applications that use them
                                        # a lot. This can speed up debugging quite a bit, but you risk not detecting
                                        # unhandled C++ exceptions. These will cause the application to terminate if
                                        # this setting is enabled, so you may want to look out for and investigate
                                        # unexpected application termination.
  "bIgnoreWinRTExceptions": False,      # Can be used to ignore Windows Runtime exceptions completely in applications
                                        # that use them a lot. This can speed up debugging quite a bit, but you risk
                                        # not detecting unhandled WinRT exceptions. These will cause the application to
                                        # terminate if this setting is enabled, so you may want to look out for and
                                        # investigate unexpected application termination.
  "bIgnoreFirstChanceNULLPointerAccessViolations": False,
  ### HTML Report debug output settings
  "bLogInReport": False,                # Log relevant events in the HTML report
  "bShowAllCdbCommandsInReport": False, # Set to True to see all commands that are executed in cdb by BugId. Set to
                                        # False to let BugId determine what to show based on the
                                        # bShowInformativeCdbCommandsInReport setting below. Note that setting this
                                        # to True can result in high memory usage, slower debugging and large reports.
                                        # Only really useful when tracking down an internal BugId error.
  "bShowInformativeCdbCommandsInReport": False, # Set to True to see the most informative commands that are executed in
                                        # cdb by BugId and the output returned by them. This includes commands that are
                                        # executed to gather information about exceptions, memory contents, disassebly,
                                        # the binaries, etc. This can be useful if you are not getting enough
                                        # information from the information BugId gathers in a report by default.
                                        # Set to False to see only cdb output returned while running the application
                                        # (this can contain both cdb and application output). In most cases, you won't
                                        # need to switch this to True. If you do; you should consider contacting the
                                        # author to ask if the information you are looking for can be included in the
                                        # report by default, rather than having to flip this setting.
  ### Page heap
  "bEnsurePageHeap": True,              # If True, each process that BugId attaches to, creates, or which is created
                                        # during debugging will be checked to make sure page heap is enabled.
                                        # If page heap is not enabled as expected, an error is reported through the
                                        # error callback. If False, BugId will only make sure page heap is enabled
                                        # when a bug is detected.
  ### UWP applications
  "nUWPApplicationAttachTimeout": 10,   # The number of seconds to wait for an UWP application to start.
  ### cdb limits
  "uReservedMemory": 10 * uMegaByte,    # Reserve some memory for analysis of crashes. This memory is freed before
                                        # analysis of an exception starts and reallocated if the exception was not
                                        # found to be a bug. If the memory limits applied to the application and/or
                                        # its processes do not prevent a system-wide low-memory situation, this may
                                        # allow BugId to continue operating as expected.
  "auColleteralPoisonValues": [],             # Values to be used in fake "read" operations for colleteral bug reports.
};