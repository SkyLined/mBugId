import re;
#from cException import cException; # moved to end of file to prevent circular reference
from dtsTypeId_and_sSecurityImpact_by_uExceptionCode import dtsTypeId_and_sSecurityImpact_by_uExceptionCode;
from fduStructureData import fduStructureData;
from fuStructureSize import fuStructureSize;

# Some defines.
SE01 = 0x53453031;
SE02 = 0x53453032;
W32E = 0x57333245;
STOW = 0x53544F57;
CLR1 = 0x434C5231;
LEO1 = 0x4C454F31;
# Not in the specs, but exists in the real world:
LMAX = 0x4C4D4158;

class cStowedException(object):
  def __init__(oStowedException, uCode, uAddress = None, pStackTrace = None, uStackTraceSize = 0, sErrorText = None, oNestedException = None):
    oStowedException.uCode = uCode;
    oStowedException.uAddress = uAddress;
    oStowedException.pStackTrace = pStackTrace; # dpS {pStackTrace} L{uStackTraceSize}
    oStowedException.uStackTraceSize = uStackTraceSize;
    oStowedException.sErrorText = sErrorText;
    oStowedException.oNestedException = oNestedException;
    oStowedException.sTypeId = None;
    oStowedException.sDescription = None;
    oStowedException.sSecurityImpact = None;
  
  @classmethod
  def faoCreate(cSelf, oCdbWrapper, papStowedExceptionInformation, uStowedExceptionAddressesCount):
    aoStowedExceptions = [];
    for uIndex in xrange(uStowedExceptionAddressesCount):
      pStowedExceptionInformation = papStowedExceptionInformation + uIndex * oCdbWrapper.oCurrentProcess.uPointerSize;
      oStowedException = cStowedException.foCreate(oCdbWrapper, pStowedExceptionInformation);
      if not oCdbWrapper.bCdbRunning: return None;
      aoStowedExceptions.append(oStowedException);
    return aoStowedExceptions;

  @classmethod
  def foCreate(cSelf, oCdbWrapper, pStowedExceptionInformation):
    # Read STOWED_EXCEPTION_INFORMATION_V1 or STOWED_EXCEPTION_INFORMATION_V2 structure.
    # (See https://msdn.microsoft.com/en-us/library/windows/desktop/dn600343(v=vs.85).aspx)
    # Both start with a STOWED_EXCEPTION_INFORMATION_HEADER structure.
    # (See https://msdn.microsoft.com/en-us/library/windows/desktop/dn600342(v=vs.85).aspx)
    # STOWED_EXCEPTION_INFORMATION_HEADER = {
    #   ULONG     Size
    #   ULONG     Signature      // "SE01" (0x53453031), "SE02" (0x53453032)
    # }
    dxStowedExceptionInformationHeaderStructure = [
      ("Size", 4),
      ("Signature", 4),
    ];
    uStowedExceptionInformationHeaderStructureSize = fuStructureSize(dxStowedExceptionInformationHeaderStructure);
    auStowedExceptionInformationBytes = oCdbWrapper.fauGetBytes(
      uAddress = pStowedExceptionInformation,
      uSize = uStowedExceptionInformationHeaderStructureSize,
      sComment = "Get STOWED_EXCEPTION_INFORMATION structure header",
    );
    if not oCdbWrapper.bCdbRunning: return None;
    duStowedExceptionInformationHeader = fduStructureData(auStowedExceptionInformationBytes, dxStowedExceptionInformationHeaderStructure);
    uRemainingSize = duStowedExceptionInformationHeader["Size"] - uStowedExceptionInformationHeaderStructureSize;
    uSignature = duStowedExceptionInformationHeader["Signature"];
    assert uSignature in [SE01, SE02], \
        "Unexpected signature 0x%X" % uSignature;
    # Read the remainder of the STOWED_EXCEPTION_INFORMATION_V1 or STOWED_EXCEPTION_INFORMATION_V2 structure.
    # typedef struct _STOWED_EXCEPTION_INFORMATION_V2 {
    #   STOWED_EXCEPTION_INFORMATION_HEADER Header;
    #   HRESULT                             ResultCode;
    #   struct {
    #     DWORD ExceptionForm  :2;
    #     DWORD ThreadId  :30;
    #   };
    #   union {
    #     struct {
    #       PVOID ExceptionAddress;
    #       ULONG StackTraceWordSize;
    #       ULONG StackTraceWords;
    #       PVOID StackTrace;
    #     };
    #     struct {
    #       PWSTR ErrorText;
    #     };
    #   };
    #   ULONG                               NestedExceptionType;
    #   PVOID                               NestedException;
    # } STOWED_EXCEPTION_INFORMATION_V2, *PSTOWED_EXCEPTION_INFORMATION_V2;
    dxStowedExceptionInformationStructure = dxStowedExceptionInformationHeaderStructure + [
      ("ResultCode", 4),
      ("ExceptionForm_ThreadId", 4),
      ("ExceptionAddress_ErrorTest", oCdbWrapper.oCurrentProcess.uPointerSize),
      ("StackTraceWordSize", 4),
      ("StackTraceWords", 4),
      ("StackTrace", oCdbWrapper.oCurrentProcess.uPointerSize),
    ];
    if uSignature == SE02:
      # These fields are only available in the STOWED_EXCEPTION_INFORMATION_V2 structure identified through the Signature field.
      dxStowedExceptionInformationStructure += [
        ("NestedExceptionType", 4),
        # MSDN does not mention alignment, but a pointer must be 8 byte aligned on x64, so adding this:
        ("alignment @ 0x24", oCdbWrapper.oCurrentProcess.uPointerSize == 8 and 4 or 0),
        ("NestedException", oCdbWrapper.oCurrentProcess.uPointerSize),
      ];
    assert duStowedExceptionInformationHeader["Size"] == fuStructureSize(dxStowedExceptionInformationStructure), \
        "STOWED_EXCEPTION_INFORMATION structure is 0x%X bytes, but should be 0x%X" % \
        (duStowedExceptionInformationHeader["Size"], fuStructureSize(dxStowedExceptionInformationStructure));
    auStowedExceptionInformationBytes += oCdbWrapper.fauGetBytes(
      uAddress = pStowedExceptionInformation + uStowedExceptionInformationHeaderStructureSize,
      uSize = uRemainingSize,
      sComment = "Get STOWED_EXCEPTION_INFORMATION structure after header",
    );
    if not oCdbWrapper.bCdbRunning: return None;
    duStowedExceptionInformation = fduStructureData(auStowedExceptionInformationBytes, dxStowedExceptionInformationStructure);
    # Split unions and bitfields.
    duStowedExceptionInformation["ExceptionForm"] = duStowedExceptionInformation["ExceptionForm_ThreadId"] >> 30;
    duStowedExceptionInformation["ThreadId"] = (duStowedExceptionInformation["ExceptionForm_ThreadId"] & 0xfffffffc) << 2;
    del duStowedExceptionInformation["ExceptionForm_ThreadId"];
    if uSignature == SE01:
      oNestedException = None;
    elif duStowedExceptionInformation["NestedExceptionType"] == W32E:
      oNestedException = cException.foCreateFromMemory(oCdbWrapper,
        uExceptionRecordAddress = duStowedExceptionInformation["NestedException"],
      );
    elif duStowedExceptionInformation["NestedExceptionType"] == STOW:
      oNestedException = cStowedException.foCreate(oCdbWrapper,
        uStowedExceptionAddress = duStowedExceptionInformation["NestedException"],
      );
    elif duStowedExceptionInformation["NestedExceptionType"] == CLR1:
      oNestedException = None; # TODO
    elif duStowedExceptionInformation["NestedExceptionType"] == LEO1:
      oNestedException = None; # TODO
    else:
      raise AssertionFailure("Unknown nested exception type 0x%X" % duStowedExceptionInformation["NestedExceptionType"]);
    
    # Handle the two different forms:
    if duStowedExceptionInformation["ExceptionForm"] == 1:
      oStowedException = cSelf(
        uCode = duStowedExceptionInformation["ResultCode"],
        uAddress = duStowedExceptionInformation["ExceptionAddress_ErrorTest"],
        pStackTrace = duStowedExceptionInformation["StackTrace"],
        uStackTraceSize = duStowedExceptionInformation["StackTraceWords"] * duStowedExceptionInformation["StackTraceWordSize"],
        oNestedException = oNestedException,
      );
    else:
      assert duStowedExceptionInformation["ExceptionForm"] == 2, \
          "Unexpected exception form %d" % uExceptionForm;
      sErrorText = oCdbWrapper.fsGetUnicodeString(
        uAddress = duStowedExceptionInformation["ExceptionAddress_ErrorTest"],
        sComment = "Stowed exception error text",
      );
      if not oCdbWrapper.bCdbRunning: return None;
      oStowedException = cSelf(
        uCode = duStowedExceptionInformation["ResultCode"],
        sErrorText = sErrorText,
        oNestedException = oNestedException,
      );
    
    # Create an exception id that uniquely identifies the exception and a description of the exception.
    if oStowedException.uCode in dtsTypeId_and_sSecurityImpact_by_uExceptionCode:
      oStowedException.sTypeId, oStowedException.sSecurityImpact = dtsTypeId_and_sSecurityImpact_by_uExceptionCode[oStowedException.uCode];
    else:
      oStowedException.sTypeId = "0x%08X" % oStowedException.uCode;
      oStowedException.sSecurityImpact = "Unknown";
    
    oStowedException.sTypeId += "(Stowed)";
    oStowedException.sDescription = "Stowed exception code 0x%08X" % oStowedException.uCode;
    return oStowedException;

from cException import cException;
