import re;
#from cException import cException; # moved to end of file to prevent circular reference
from .fsGetCPPObjectClassNameFromVFTable import fsGetCPPObjectClassNameFromVFTable;
from .cWindowsStatusOrError import cWindowsStatusOrError;
from mWindowsAPI.mDefines import \
    STOWED_EXCEPTION_INFORMATION_V1_SIGNATURE, STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE, \
    STOWED_EXCEPTION_NESTED_TYPE_NONE, STOWED_EXCEPTION_NESTED_TYPE_WIN32, STOWED_EXCEPTION_NESTED_TYPE_STOWED, \
    STOWED_EXCEPTION_NESTED_TYPE_CLR, STOWED_EXCEPTION_NESTED_TYPE_LEO, STOWED_EXCEPTION_NESTED_TYPE_LMAX;
from mWindowsAPI.mTypes import \
    STOWED_EXCEPTION_INFORMATION_HEADER, \
    STOWED_EXCEPTION_INFORMATION_V1_32, STOWED_EXCEPTION_INFORMATION_V1_64, \
    STOWED_EXCEPTION_INFORMATION_V2_32, STOWED_EXCEPTION_INFORMATION_V2_64;
from mWindowsAPI.mFunctions import SIZEOF;
from mWindowsAPI import cVirtualAllocation;

def fsSignature(uSignature):
  return "".join([chr((uSignature >> (uByteIndex * 8)) & 0xFF) for uByteIndex in xrange(3,-1,-1)]);

class cStowedException(object):
  def __init__(oStowedException, \
      iCode,
      uAddress = None,
      pStackTrace = None, uStackTraceSize = 0,
      sErrorText = None,
      sNestedExceptionTypeId = None,
      oNestedException = None,
      sWRTLanguageExceptionIUnkownClassName = None,
    ):
    oStowedException.iCode = iCode; # HRESULT, signed 32-bit integer (negative == error).
    uCode = iCode + (iCode < 0 and (1 << 32) or 0); # Convert to unsigned 32-bit integer.
    oStowedException.uAddress = uAddress;
    oStowedException.pStackTrace = pStackTrace; # dpS {pStackTrace} L{uStackTraceSize}
    oStowedException.uStackTraceSize = uStackTraceSize;
    oStowedException.sErrorText = sErrorText;
    oStowedException.sNestedExceptionTypeId = sNestedExceptionTypeId;
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
      oStowedException.sDescription = "Unknown exception code 0x%08X." % uCode;
    if oStowedException.sErrorText:
      oStowedException.sDescription += " Error: %s" % oStowedException.sErrorText;
    if sNestedExceptionTypeId:
      oStowedException.sTypeId += ":%s" % (sNestedExceptionTypeId,);
      if oStowedException.oNestedException:
        oStowedException.sTypeId += "(%s)" % (sNestedExceptionTypeId, oStowedException.oNestedException.sTypeId);
        oStowedException.sDescription += " Nested %s exception: %s." % \
            (sNestedExceptionTypeId, oStowedException.oNestedException.sDescription);
        oStowedException.sSecurityImpact = " Nested %s exception: %s." % \
            (sNestedExceptionTypeId, oStowedException.oNestedException.sSecurityImpact);
    if oStowedException.sWRTLanguageExceptionIUnkownClassName:
      oStowedException.sTypeId += "@%s" % oStowedException.sWRTLanguageExceptionIUnkownClassName;
      oStowedException.sDescription += " WRT Language exception class name: %s." % oStowedException.sWRTLanguageExceptionIUnkownClassName;
  
  @staticmethod
  def faoCreate(oProcess, uauStowedExceptionInformationAddressesAddress, uStowedExceptionInformationAddressesCount):
    auStowedExceptionInformationAddresses = oProcess.fauReadPointersForAddressAndCount(
      uAddress = uauStowedExceptionInformationAddressesAddress,
      uCount = uStowedExceptionInformationAddressesCount,
    );
    return [
      cStowedException.foCreate(oProcess, uStowedExceptionInformationAddress)
      for uStowedExceptionInformationAddress in auStowedExceptionInformationAddresses
    ];

  @staticmethod
  def foCreate(oProcess, uStowedExceptionInformationAddress):
    # Read STOWED_EXCEPTION_INFORMATION_V1 or STOWED_EXCEPTION_INFORMATION_V2 structure.
    # (See https://msdn.microsoft.com/en-us/library/windows/desktop/dn600343(v=vs.85).aspx)
    # Both start with a STOWED_EXCEPTION_INFORMATION_HEADER structure.
    # (See https://msdn.microsoft.com/en-us/library/windows/desktop/dn600342(v=vs.85).aspx)
    # STOWED_EXCEPTION_INFORMATION_HEADER = {
    #   ULONG     Size
    #   ULONG     Signature      // "SE01" (0x53453031), "SE02" (0x53453032)
    # }
    oStowedExceptionInformationHeader = oProcess.foReadStructureForAddress(
      cStructure = STOWED_EXCEPTION_INFORMATION_HEADER,
      uAddress = uStowedExceptionInformationAddress,
    );
    if oStowedExceptionInformationHeader.Signature == STOWED_EXCEPTION_INFORMATION_V1_SIGNATURE:
      cStowedExceptionInformation = {
        "x86": STOWED_EXCEPTION_INFORMATION_V1_32,
        "x64": STOWED_EXCEPTION_INFORMATION_V1_64,
      }[oProcess.sISA];
    else:
      assert oStowedExceptionInformationHeader.Signature == STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE, \
          "Unexpected stowed exception signature 0x%X (expected 0x%X or 0x%X)" % \
          (oStowedExceptionInformationHeader.Signature, STOWED_EXCEPTION_INFORMATION_V1_SIGNATURE, \
          STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE);
      cStowedExceptionInformation = {
        "x86": STOWED_EXCEPTION_INFORMATION_V2_32,
        "x64": STOWED_EXCEPTION_INFORMATION_V2_64,
      }[oProcess.sISA];
    assert oStowedExceptionInformationHeader.Size == SIZEOF(cStowedExceptionInformation), \
        "STOWED_EXCEPTION_INFORMATION structure is 0x%X bytes, but 0x%X was expected!?" % \
        (oStowedExceptionInformationHeader.Size, SIZEOF(cStowedExceptionInformation));
    oStowedExceptionInformation = oProcess.foReadStructureForAddress(
      cStructure = cStowedExceptionInformation,
      uAddress = uStowedExceptionInformationAddress,
    );
    uExceptionForm = oStowedExceptionInformation.ExceptionForm_ThreadId & 3;
    uThreadId = (oStowedExceptionInformation.ExceptionForm_ThreadId & 0xfffffffc) << 2;
    # Handle structure
    sNestedExceptionTypeId = None;
    oNestedException = None;
    sWRTLanguageExceptionIUnkownClassName = None;
    if (
      oStowedExceptionInformationHeader.Signature == STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE
      and oStowedExceptionInformation.NestedExceptionType != STOWED_EXCEPTION_NESTED_TYPE_NONE
    ):
      if oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_WIN32:
        sNestedExceptionTypeId = "Win32";
        oNestedException = cException.foCreateFromMemory(
          oProcess = oProcess,
          uExceptionRecordAddress = oStowedExceptionInformation.NestedException,
        );
      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_STOWED:
        sNestedExceptionTypeId = "Stowed";
        oNestedException = cStowedException.foCreate(
          oProcess = oProcess,
          uStowedExceptionAddress = oStowedExceptionInformation.NestedException,
        );
      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_CLR:
        sNestedExceptionTypeId = "CLR";
        # TODO: find out how to trigger these so I can find out how to handle them.
      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_LEO:
        sNestedExceptionTypeId = "WRTLanguage";
        # These can be triggered using RoOriginateLanguageException. The "NestedException" contains a pointer to an
        # object that implements IUnknown. Apparently this object "contains all the information necessary recreate it
        # the exception a later point." (https://msdn.microsoft.com/en-us/library/dn302172(v=vs.85).aspx)
        # I have not been able to find more documentation for this, so this is based on reverse engineering.
        sWRTLanguageExceptionIUnkownClassName = fsGetCPPObjectClassNameFromVFTable(
          oProcess = oProcess,
          uCPPObjectAddress = oStowedExceptionInformation.NestedException,
        );
#      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_LMAX:
      else:
        uDataAddress = oStowedExceptionInformation.NestedException;
        oDataVirtualAllocation = cVirtualAllocation(oProcess.uId, uDataAddress);
        uDataOffset = uDataAddress - oDataVirtualAllocation.uStartAddress;
        uDataSize = min(0x80, oDataVirtualAllocation.uSize - uDataOffset);
        sData = ",".join([
          "%02X" % uByte
          for uByte in oDataVirtualAllocation.fauReadBytesForOffsetAndSize(uDataOffset, uDataSize)
        ]);
        sNestedExceptionTypeId = "Type=0x%08X,Data@0x%08X:[%s]" % \
            (oStowedExceptionInformation.NestedExceptionType, uDataAddress, sData);
    # Handle the two different forms:
    if uExceptionForm == 1:
      oStowedException = cStowedException(
        iCode = oStowedExceptionInformation.ResultCode,
        uAddress = oStowedExceptionInformation.ExceptionAddress,
        pStackTrace = oStowedExceptionInformation.StackTrace,
        uStackTraceSize = oStowedExceptionInformation.StackTraceWords * oStowedExceptionInformation.StackTraceWordSize,
        sNestedExceptionTypeId = sNestedExceptionTypeId,
        oNestedException = oNestedException,
        sWRTLanguageExceptionIUnkownClassName = sWRTLanguageExceptionIUnkownClassName,
      );
    else:
      assert uExceptionForm == 2, \
          "Unexpected exception form %d" % uExceptionForm;
      sErrorText = oProcess.fsReadNullTerminatedStringForAddress(
        uAddress = oStowedExceptionInformation.ErrorText,
        bUnicode = True,
      );
      oStowedException = cStowedException(
        iCode = oStowedExceptionInformation.ResultCode,
        sErrorText = sErrorText,
        sNestedExceptionTypeId = sNestedExceptionTypeId,
        oNestedException = oNestedException,
        sWRTLanguageExceptionIUnkownClassName = sWRTLanguageExceptionIUnkownClassName,
      );
    
    return oStowedException;

from cException import cException;
