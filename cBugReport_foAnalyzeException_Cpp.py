from mWindowsAPI.mFunctions import STR;
from mWindowsAPI.mTypes import BYTE, DWORD, fcStructure, PVOID_32, PVOID_64;
from mWindowsAPI import cVirtualAllocation, mDbgHelp;

EXCEPTION_OBJECT_DESCRIPTION_1 = fcStructure("EXCEPTION_OBJECT_DESCRIPTION_1",
  (DWORD,           "dwUnknown_1"),
  (DWORD,           "dwUnknown_2"),
  (DWORD,           "dwUnknown_3"),
  (DWORD,           "uOffsetOfPart2"),
  uAlignmentBytes = 4,
);
EXCEPTION_OBJECT_DESCRIPTION_2 = fcStructure("EXCEPTION_OBJECT_DESCRIPTION_2",
  (DWORD,           "dwUnknown_1"),
  (DWORD,           "uOffsetOfPart3"),
  uAlignmentBytes = 4,
);
EXCEPTION_OBJECT_DESCRIPTION_3 = fcStructure("EXCEPTION_OBJECT_DESCRIPTION_3",
  (DWORD,           "dwUnknown_1"),
  (DWORD,           "uOffsetOfPart4"),
  uAlignmentBytes = 4,
);
guMaxSymbolName = 0x20; # Don't know, but don't care at this point either...
EXCEPTION_OBJECT_DESCRIPTION_4_32 = fcStructure("EXCEPTION_OBJECT_DESCRIPTION_4_32",
  (PVOID_32,           "pUnknown_1"),
  (PVOID_32,           "pUnknown_2"),
  (BYTE * guMaxSymbolName, "szDecoratedClassName"),
  uAlignmentBytes = 4,
);
EXCEPTION_OBJECT_DESCRIPTION_4_64 = fcStructure("EXCEPTION_OBJECT_DESCRIPTION_4_64",
  (PVOID_64,           "pUnknown_1"),
  (PVOID_64,           "pUnknown_2"),
  (BYTE * guMaxSymbolName, "szDecoratedClassName"),
  uAlignmentBytes = 8,
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
  uExceptionObjectDescriptionAddress = oException.auParameters[2];
  oExceptionObjectDescriptionVirtualAllocation = cVirtualAllocation(oProcess.uId, uExceptionObjectDescriptionAddress);
  oExceptionObjectDescription = oExceptionObjectDescriptionVirtualAllocation.foReadStructureForOffset(
    EXCEPTION_OBJECT_DESCRIPTION_1,
    uExceptionObjectDescriptionAddress - oExceptionObjectDescriptionVirtualAllocation.uStartAddress,
  );
  # PART 2
  uAddressOfPart2 = uBaseAddress + oExceptionObjectDescription.uOffsetOfPart2;
  oPart2VirtualAllocation = cVirtualAllocation(oProcess.uId, uAddressOfPart2);
  oPart2 = oPart2VirtualAllocation.foReadStructureForOffset(
    EXCEPTION_OBJECT_DESCRIPTION_2,
    uAddressOfPart2 - oPart2VirtualAllocation.uStartAddress,
  );
  # PART 3
  uAddressOfPart3 = uBaseAddress + oPart2.uOffsetOfPart3;
  oPart3VirtualAllocation = cVirtualAllocation(oProcess.uId, uAddressOfPart3);
  oPart3 = oPart3VirtualAllocation.foReadStructureForOffset(
    EXCEPTION_OBJECT_DESCRIPTION_3,
    uAddressOfPart3 - oPart3VirtualAllocation.uStartAddress,
  );
  # PART 4
  uAddressOfPart4 = uBaseAddress + oPart3.uOffsetOfPart4;
  oPart4VirtualAllocation = cVirtualAllocation(oProcess.uId, uAddressOfPart4);
  cStructureOfPart4 = {
    "x86": EXCEPTION_OBJECT_DESCRIPTION_4_32,
    "x64": EXCEPTION_OBJECT_DESCRIPTION_4_64,
  }[oProcess.sISA]; 
  oPart4 = oPart4VirtualAllocation.foReadStructureForOffset(
    cStructureOfPart4,
    uAddressOfPart4 - oPart4VirtualAllocation.uStartAddress,
  );
  # Extract decorated symbol name of class from part 4
  uAddressOfDecoratedClassName = uAddressOfPart4 + oPart4.fuOffsetOf("szDecoratedClassName");
  sDecoratedClassName = oPart4VirtualAllocation.fsReadNullTerminatedStringForOffset(
    uAddressOfDecoratedClassName - oPart4VirtualAllocation.uStartAddress
  );
  sClassName = mDbgHelp.fsUndecorateSymbolName(sDecoratedClassName, bNameOnly = True);
  # Get undecorated symbol name of class and add it to the exception:
  oBugReport.sBugTypeId += ":%s" % (sClassName or sDecoratedClassName);
  return oBugReport;
