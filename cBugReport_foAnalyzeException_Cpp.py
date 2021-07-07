from mWindowsSDK import *;
from mWindowsAPI import cVirtualAllocation, mDbgHelp;

EXCEPTION_OBJECT_DESCRIPTION_1 = iStructureType32.fcCreateClass("EXCEPTION_OBJECT_DESCRIPTION_1",
  (DWORD,           "dwUnknown_1"),
  (DWORD,           "dwUnknown_2"),
  (DWORD,           "dwUnknown_3"),
  (DWORD,           "uOffsetOfPart2"),
);
EXCEPTION_OBJECT_DESCRIPTION_2 = iStructureType32.fcCreateClass("EXCEPTION_OBJECT_DESCRIPTION_2",
  (DWORD,           "dwUnknown_1"),
  (DWORD,           "uOffsetOfPart3"),
);
EXCEPTION_OBJECT_DESCRIPTION_3 = iStructureType32.fcCreateClass("EXCEPTION_OBJECT_DESCRIPTION_3",
  (DWORD,           "dwUnknown_1"),
  (DWORD,           "uOffsetOfPart4"),
);
guMaxSymbolName = 0x20; # Don't know, but don't care at this point either...
EXCEPTION_OBJECT_DESCRIPTION_4_32 = iStructureType32.fcCreateClass("EXCEPTION_OBJECT_DESCRIPTION_4_32",
  (P32VOID,         "pUnknown_1"),
  (P32VOID,         "pUnknown_2"),
  (CHAR[guMaxSymbolName], "szDecoratedClassName"),
);
EXCEPTION_OBJECT_DESCRIPTION_4_64 = iStructureType64.fcCreateClass("EXCEPTION_OBJECT_DESCRIPTION_4_64",
  (P64VOID,         "pUnknown_1"),
  (P64VOID,         "pUnknown_2"),
  (CHAR[guMaxSymbolName], "szDecoratedClassName"),
);

def cBugReport_foAnalyzeException_Cpp(oBugReport, oProcess, oThread, oException):
  # Based on https://blogs.msdn.microsoft.com/oldnewthing/20100730-00/?p=13273/
  # Attempt to get the symbol of the virtual function table of the object that was thrown and add that the the type id:
  if oProcess.sISA == "x64":
    assert len(oException.auParameters) == 4, \
        "Expected a C++ Exception to have 4 parameters, got %d" % len(oException.auParameters);
    # On 64-bit systems, the exception information uses 32-bit offsets from a 64-bit base address.
    uBaseAddress = oException.auParameters[3];
  else:
    assert len(oException.auParameters) == 3, \
        "Expected a C++ Exception to have 3 parameters, got %d" % len(oException.auParameters);
    # On 32-bit systems, the exception information uses 32-bit addresses (== offsets from 0).
    uBaseAddress = 0;
    # +-------+ 
    # | DW/QW | uUnknown1
    # +-------+
    # | DW/QW | uExceptionObjectAddress*            (may not be actual address)
    # +-------+ 
    # | DW/QW | uExceptionObjectDescriptionAddress
    # +-------+               |
    # | DW/QW | uBaseAddress* |                        (optional, 64-bit only!)
    # +-------+  |            |
    #            |    ,----- -'
    #            |    V
    #            |  +----+ EXCEPTION_OBJECT_DESCRIPTION_1
    #            |  | DW | uUnknown1
    #            |  +----+ 
    #            |  | DW | uUnknown2
    #            |  +----+ 
    #            |  | DW | uUnknown3
    #            |  +----+ 
    #            |  | DW | uOffsetOfPart2
    #            |  +----+  |
    #            |  :    :  |
    #            |          |
    #            |'--------.|
    #            |          V
    #            |        +----+ EXCEPTION_OBJECT_DESCRIPTION_2
    #            |        | DW | uUnknown1
    #            |        +----+
    #            |        | DW | uOffsetOfPart3
    #            |        +----+  |
    #            |        :    :  |
    #            |                |
    #            |'--------------.|
    #            |                V
    #            |              +----+ EXCEPTION_OBJECT_DESCRIPTION_3
    #            |              | DW | uUnknown1
    #            |              +----+
    #            |              | DW | uOffsetOfPart4
    #            |              +----+  |
    #            |              :    :  |
    #            |                      |
    #             '--------------------.|
    #                                   V
    #                                  +-------+ EXCEPTION_OBJECT_DESCRIPTION_4
    #                                  | DW/QW | uAddressOfVFTable
    #                                  +-------+
    #                                  | DW/QW | uUnknown1
    #                                  +-------+
    #                                  | CHARS | szClassName
    #                                  :       :
  # PART 1
  o0ExceptionObjectDescription = oProcess.fo0ReadStructureForAddress(
    EXCEPTION_OBJECT_DESCRIPTION_1,
    oException.auParameters[2],
  );
  if o0ExceptionObjectDescription:
    # PART 2
    o0Part2 = oProcess.fo0ReadStructureForAddress(
      EXCEPTION_OBJECT_DESCRIPTION_2,
      uBaseAddress + o0ExceptionObjectDescription.uOffsetOfPart2.fuGetValue(),
    );
    if o0Part2:
      # PART 3
      o0Part3 = oProcess.fo0ReadStructureForAddress(
        EXCEPTION_OBJECT_DESCRIPTION_3,
        uBaseAddress + o0Part2.uOffsetOfPart3.fuGetValue(),
      );
      if o0Part3:
        # PART 4
        cStructureOfPart4 = {
          "x86": EXCEPTION_OBJECT_DESCRIPTION_4_32,
          "x64": EXCEPTION_OBJECT_DESCRIPTION_4_64,
        }[oProcess.sISA]; 
        o0Part4 = oProcess.fo0ReadStructureForAddress(
          cStructureOfPart4,
          uBaseAddress + o0Part3.uOffsetOfPart4.fuGetValue(),
        );
        if o0Part4:
          # Extract decorated symbol name of class from part 4
          s0DecoratedClassName = oProcess.fs0ReadNullTerminatedStringForAddress(
            uBaseAddress + o0Part3.uOffsetOfPart4.fuGetValue() + o0Part4.fuGetOffsetOfMember("szDecoratedClassName")
          );
          if s0DecoratedClassName:
            # Undecorate the symbol name
            s0UndecoratedClassName = mDbgHelp.fs0UndecorateSymbolName(s0DecoratedClassName, bNameOnly = True);
            # If we can undecorate the symbol name of the class, add it to the exception, otherwise add the decorated
            # one (which is most likely already undecorated to begin with):
            assert oBugReport.s0BugTypeId is not None, \
                "oBugReport.s0BugTypeId shouldn't be None at this point";
            oBugReport.s0BugTypeId += ":%s" % (s0UndecoratedClassName or s0DecoratedClassName);
  return oBugReport;
