import re;
#from cException import cException; # moved to end of file to prevent circular reference
from fduStructureData import fduStructureData;
from fsGetCPPObjectClassNameFromVFTable import fsGetCPPObjectClassNameFromVFTable;
from fuStructureSize import fuStructureSize;
from cWindowsStatusOrError import cWindowsStatusOrError;

def fsSignature(uSignature):
  return "".join([chr((uSignature >> (uByteIndex * 8)) & 0xFF) for uByteIndex in xrange(3,-1,-1)]);

class cStowedException(object):
  def __init__(oStowedException, \
      uCode,
      uAddress = None,
      pStackTrace = None, uStackTraceSize = 0,
      sErrorText = None,
      oNestedException = None,
      sWRTLanguageExceptionIUnkownClassName = None,
    ):
    oStowedException.uCode = uCode;
    oStowedException.uAddress = uAddress;
    oStowedException.pStackTrace = pStackTrace; # dpS {pStackTrace} L{uStackTraceSize}
    oStowedException.uStackTraceSize = uStackTraceSize;
    oStowedException.sErrorText = sErrorText;
    oStowedException.oNestedException = oNestedException;
    oStowedException.sWRTLanguageExceptionIUnkownClassName = sWRTLanguageExceptionIUnkownClassName;
    # Create an exception id that uniquely identifies the exception and a description of the exception.
    oWindowsStatusOrError = cWindowsStatusOrError.foGetForCode(uCode);
    if oWindowsStatusOrError:
      oStowedException.sTypeId = oWindowsStatusOrError.sTypeId;
      oStowedException.sSecurityImpact = oWindowsStatusOrError.sSecurityImpact;
      oStowedException.sDescription = oWindowsStatusOrError.sDescription;
    else:
      oStowedException.sTypeId = "0x%08X" % uCode;
      oStowedException.sSecurityImpact = "Unknown";
      oStowedException.sDescription = "Unknown exception code 0x%08X" % uCode;
    if oStowedException.sErrorText:
      oStowedException.sDescription += " Error: %s" % oStowedException.sErrorText;
    if oStowedException.oNestedException:
      oStowedException.sTypeId += "[%s]" % oStowedException.oNestedException.sTypeId;
      oStowedException.sDescription += " Nested exception: %s." % oStowedException.oNestedException.sDescription;
      oStowedException.sSecurityImpact = " Nested exception: %s." % oStowedException.oNestedException.sSecurityImpact;
    if oStowedException.sWRTLanguageExceptionIUnkownClassName:
      oStowedException.sTypeId += "@%s" % oStowedException.sWRTLanguageExceptionIUnkownClassName;
      oStowedException.sDescription += " WRT Language exception class name: %s." % oStowedException.sWRTLanguageExceptionIUnkownClassName;
  
  @staticmethod
  def faoCreate(oProcess, papStowedExceptionInformation, uStowedExceptionAddressesCount):
    aoStowedExceptions = [];
    for uIndex in xrange(uStowedExceptionAddressesCount):
      ppStowedExceptionInformation = papStowedExceptionInformation + uIndex * oProcess.uPointerSize;
      pStowedExceptionInformation = oProcess.fuGetValue("poi(0x%X)" % ppStowedExceptionInformation, "Get stowed exception pointer #%d" % uIndex);
      oStowedException = cStowedException.foCreate(oProcess, pStowedExceptionInformation);
      aoStowedExceptions.append(oStowedException);
    return aoStowedExceptions;

  @staticmethod
  def foCreate(oProcess, pStowedExceptionInformation):
    # Read STOWED_EXCEPTION_INFORMATION_V1 or STOWED_EXCEPTION_INFORMATION_V2 structure.
    # (See https://msdn.microsoft.com/en-us/library/windows/desktop/dn600343(v=vs.85).aspx)
    # Both start with a STOWED_EXCEPTION_INFORMATION_HEADER structure.
    # (See https://msdn.microsoft.com/en-us/library/windows/desktop/dn600342(v=vs.85).aspx)
    # STOWED_EXCEPTION_INFORMATION_HEADER = {
    #   ULONG     Size
    #   ULONG     Signature      // "SE01" (0x53453031), "SE02" (0x53453032)
    # }
    axStowedExceptionInformationHeaderStructure = [
      ("Size", 4),
      ("Signature", 4),
    ];
    uStowedExceptionInformationHeaderStructureSize = fuStructureSize(axStowedExceptionInformationHeaderStructure);
    auStowedExceptionInformationBytes = oProcess.fauGetBytes(
      uAddress = pStowedExceptionInformation,
      uSize = uStowedExceptionInformationHeaderStructureSize,
      sComment = "Get STOWED_EXCEPTION_INFORMATION_HEADER",
    );
    duStowedExceptionInformationHeader = fduStructureData(auStowedExceptionInformationBytes, axStowedExceptionInformationHeaderStructure);
    uRemainingSize = duStowedExceptionInformationHeader["Size"] - uStowedExceptionInformationHeaderStructureSize;
    uSignature = duStowedExceptionInformationHeader["Signature"];
    sSignature = "".join([
      chr((uSignature >> (uByteIndex * 8)) & 0xFF)
      for uByteIndex in xrange(3,-1,-1)
    ]);
    assert sSignature in ["SE01", "SE02"], \
        "Unexpected signature 0x%X (%s)" % (uSignature, sSignature);
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
    axStowedExceptionInformationStructure = axStowedExceptionInformationHeaderStructure + [
      ("ResultCode", 4),
      ("ExceptionForm_ThreadId", 4),
      ("ExceptionAddress_ErrorText", oProcess.uPointerSize),
      ("StackTraceWordSize", 4),
      ("StackTraceWords", 4),
      ("StackTrace", oProcess.uPointerSize),
    ];
    if sSignature == "SE02":
      # These fields are only available in the STOWED_EXCEPTION_INFORMATION_V2 structure identified through the Signature field.
      axStowedExceptionInformationStructure += [
        ("NestedExceptionType", 4),
        # MSDN does not mention alignment, but a pointer must be 8 byte aligned on x64, so adding this:
        ("alignment @ 0x24", oProcess.uPointerSize == 8 and 4 or 0),
        ("NestedException", oProcess.uPointerSize),
      ];
    assert duStowedExceptionInformationHeader["Size"] == fuStructureSize(axStowedExceptionInformationStructure), \
        "STOWED_EXCEPTION_INFORMATION structure is 0x%X bytes, but should be 0x%X" % \
        (duStowedExceptionInformationHeader["Size"], fuStructureSize(axStowedExceptionInformationStructure));
    auStowedExceptionInformationBytes += oProcess.fauGetBytes(
      uAddress = pStowedExceptionInformation + uStowedExceptionInformationHeaderStructureSize,
      uSize = uRemainingSize,
      sComment = "Get remaining STOWED_EXCEPTION_INFORMATION (after the header)",
    );
    # Parse structure and split unions and bitfields.
    duStowedExceptionInformation = fduStructureData(auStowedExceptionInformationBytes, axStowedExceptionInformationStructure);
    duStowedExceptionInformation["ExceptionForm"] = duStowedExceptionInformation["ExceptionForm_ThreadId"] & 3;
    duStowedExceptionInformation["ThreadId"] = (duStowedExceptionInformation["ExceptionForm_ThreadId"] & 0xfffffffc) << 2;
    del duStowedExceptionInformation["ExceptionForm_ThreadId"];
    if duStowedExceptionInformation["ExceptionForm"] == 1:
      duStowedExceptionInformation["ExceptionAddress"] = duStowedExceptionInformation["ExceptionAddress_ErrorText"];
    else:
      duStowedExceptionInformation["ErrorText"] = duStowedExceptionInformation["ExceptionAddress_ErrorText"];
    del duStowedExceptionInformation["ExceptionAddress_ErrorText"];
    # Handle structure
    oNestedException = None;
    sWRTLanguageExceptionIUnkownClassName = None;
    uNestedExceptionType = duStowedExceptionInformation["NestedExceptionType"];
    sNestedExceptionType = uNestedExceptionType and "".join([
      chr((uNestedExceptionType >> (uByteIndex * 8)) & 0xFF)
      for uByteIndex in xrange(4)
    ]) or None;
    if sSignature == "SE02" and sNestedExceptionType is not None:
      if sNestedExceptionType == "W32E":
        oNestedException = cException.foCreateFromMemory(
          oProcess = oProcess,
          uExceptionRecordAddress = duStowedExceptionInformation["NestedException"],
        );
      elif sNestedExceptionType == "STOW":
        oNestedException = cStowedException.foCreate(
          oProcess = oProcess,
          uStowedExceptionAddress = duStowedExceptionInformation["NestedException"],
        );
      elif sNestedExceptionType == "CLR1":
        pass; # TODO
      elif sNestedExceptionType == "LEO1":
        # These can be triggered using RoOriginateLanguageException. The "NestedException" contains a pointer to an
        # object that implements IUnknown. Apparently this object "contains all the information necessary recreate it
        # the exception a later point." (https://msdn.microsoft.com/en-us/library/dn302172(v=vs.85).aspx)
        # I have not been able to find more documentation for this, so this is based on reverse engineering.
        sWRTLanguageExceptionIUnkownClassName = fsGetCPPObjectClassNameFromVFTable(
          oProcess = oProcess,
          uCPPObjectAddress = duStowedExceptionInformation["NestedException"]
        );
    # Handle the two different forms:
    if duStowedExceptionInformation["ExceptionForm"] == 1:
      oStowedException = cStowedException(
        uCode = duStowedExceptionInformation["ResultCode"],
        uAddress = duStowedExceptionInformation["ExceptionAddress"],
        pStackTrace = duStowedExceptionInformation["StackTrace"],
        uStackTraceSize = duStowedExceptionInformation["StackTraceWords"] * duStowedExceptionInformation["StackTraceWordSize"],
        oNestedException = oNestedException,
        sWRTLanguageExceptionIUnkownClassName = sWRTLanguageExceptionIUnkownClassName,
      );
    else:
      assert duStowedExceptionInformation["ExceptionForm"] == 2, \
          "Unexpected exception form %d" % duStowedExceptionInformation["ExceptionForm"];
      sErrorText = oProcess.fsGetUnicodeString(
        duStowedExceptionInformation["ErrorText"],
        "Get Stowed exception ErrorText string",
      );
      oStowedException = cStowedException(
        uCode = duStowedExceptionInformation["ResultCode"],
        sErrorText = sErrorText,
        oNestedException = oNestedException,
        sWRTLanguageExceptionIUnkownClassName = sWRTLanguageExceptionIUnkownClassName,
      );
    
    return oStowedException;

from cException import cException;
