import re;

from mWindowsSDK import *;
from mWindowsAPI import cVirtualAllocation;

#from cException import cException; # moved to end of file to prevent circular reference
from .fsGetCPPObjectClassNameFromVFTable import fsGetCPPObjectClassNameFromVFTable;
from .cErrorDetails import cErrorDetails;

def fsSignature(uSignature):
  return "".join([chr((uSignature >> (uByteIndex * 8)) & 0xFF) for uByteIndex in xrange(3,-1,-1)]);

class cStowedException(object):
  def __init__(oStowedException, \
    iCode,
    uAddress = None,
    pStackTrace = None, uStackTraceSize = 0,
    s0ErrorText = None,
    sNestedExceptionTypeId = None,
    oNestedException = None,
    sWRTLanguageExceptionIUnkownClassName = None,
  ):
    oStowedException.iCode = iCode; # HRESULT, signed 32-bit integer (negative == error).
    uCode = iCode + (iCode < 0 and (1 << 32) or 0); # Convert to unsigned 32-bit integer.
    oStowedException.uAddress = uAddress;
    oStowedException.pStackTrace = pStackTrace; # dpS {pStackTrace} L{uStackTraceSize}
    oStowedException.uStackTraceSize = uStackTraceSize;
    oStowedException.s0ErrorText = s0ErrorText;
    oStowedException.sNestedExceptionTypeId = sNestedExceptionTypeId;
    oStowedException.oNestedException = oNestedException;
    oStowedException.sWRTLanguageExceptionIUnkownClassName = sWRTLanguageExceptionIUnkownClassName;
    # Create an exception id that uniquely identifies the exception and a description of the exception.
    o0ErrorDetails = cErrorDetails.fo0GetForCode(uCode);
    if o0ErrorDetails:
      oStowedException.sTypeId = o0ErrorDetails.sTypeId;
      oStowedException.sSecurityImpact = o0ErrorDetails.s0SecurityImpact;
      oStowedException.sDescription = o0ErrorDetails.sDescription;
    else:
      oStowedException.sTypeId = "0x%08X" % uCode;
      oStowedException.sSecurityImpact = "Unknown";
      oStowedException.sDescription = "Unknown exception code 0x%08X." % uCode;
    if oStowedException.s0ErrorText:
      oStowedException.sDescription += " Error: %s" % oStowedException.s0ErrorText;
    if sNestedExceptionTypeId:
      oStowedException.sTypeId += ":%s" % (sNestedExceptionTypeId,);
      if oStowedException.oNestedException:
        oStowedException.sTypeId += "(%s)" % (oStowedException.oNestedException.sTypeId,);
        oStowedException.sDescription += " Nested %s exception: %s." % \
            (sNestedExceptionTypeId, oStowedException.oNestedException.sDescription);
        oStowedException.sSecurityImpact = " Nested %s exception: %s." % \
            (sNestedExceptionTypeId, oStowedException.oNestedException.sSecurityImpact);
    if oStowedException.sWRTLanguageExceptionIUnkownClassName:
      oStowedException.sTypeId += "@%s" % oStowedException.sWRTLanguageExceptionIUnkownClassName;
      oStowedException.sDescription += " WRT Language exception class name: %s." % oStowedException.sWRTLanguageExceptionIUnkownClassName;
  
  @staticmethod
  def faoCreateForListAddressAndCount(oProcess, uListAddress, uCount):
    a0uStowedExceptionInformationAddresses = oProcess.fa0uReadPointersForAddressAndCount(uListAddress, uCount);
    assert a0uStowedExceptionInformationAddresses, \
        "Cannot read %d stowed exception information pointers from process %d / 0x%X at address 0x%X" % \
        (uCount, oProcess.uId, oProcess.uId, uAddress);
    return [
      cStowedException.foCreate(oProcess, uStowedExceptionInformationAddress)
      for uStowedExceptionInformationAddress in a0uStowedExceptionInformationAddresses
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
    o0StowedExceptionInformationHeader = oProcess.fo0ReadStructureForAddress(
      cStructure = STOWED_EXCEPTION_INFORMATION_HEADER,
      uAddress = uStowedExceptionInformationAddress,
    );
    assert o0StowedExceptionInformationHeader, \
        "Cannot read stowed exception information header from process %d / 0x%X at address 0x%X!" % \
        (oProcess.uId, oProcess.uId, uStowedExceptionInformationAddress);
    oStowedExceptionInformationHeader = o0StowedExceptionInformationHeader;
    if oStowedExceptionInformationHeader.Signature == STOWED_EXCEPTION_INFORMATION_V1_SIGNATURE:
      cStowedExceptionInformation = {
        "x86": STOWED_EXCEPTION_INFORMATION_V132,
        "x64": STOWED_EXCEPTION_INFORMATION_V164,
      }[oProcess.sISA];
    else:
      assert oStowedExceptionInformationHeader.Signature == STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE, \
          "Unexpected stowed exception signature 0x%X (expected 0x%X or 0x%X)" % \
          (oStowedExceptionInformationHeader.Signature, STOWED_EXCEPTION_INFORMATION_V1_SIGNATURE, \
          STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE);
      cStowedExceptionInformation = {
        "x86": STOWED_EXCEPTION_INFORMATION_V232,
        "x64": STOWED_EXCEPTION_INFORMATION_V264,
      }[oProcess.sISA];
    assert oStowedExceptionInformationHeader.Size == cStowedExceptionInformation.fuGetSize(), \
        "STOWED_EXCEPTION_INFORMATION structure is 0x%X bytes, but 0x%X was expected!?" % \
        (oStowedExceptionInformationHeader.Size, cStowedExceptionInformation.fuGetSize());
    o0StowedExceptionInformation = oProcess.fo0ReadStructureForAddress(
      cStructure = cStowedExceptionInformation,
      uAddress = uStowedExceptionInformationAddress,
    );
    assert o0StowedExceptionInformation, \
        "Cannot read stowed exception information from process %d / 0x%X at address 0x%X!" % \
        (oProcess.uId, oProcess.uId, uStowedExceptionInformationAddress);
    oStowedExceptionInformation = o0StowedExceptionInformation;
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
      uNestedExceptionAddress = oStowedExceptionInformation.NestedException.value;
      if oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_WIN32:
        sNestedExceptionTypeId = "Win32";
        oNestedException = cException.foCreateFromMemory(
          oProcess = oProcess,
          uExceptionRecordAddress = uNestedExceptionAddress,
        );
      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_STOWED:
        sNestedExceptionTypeId = "Stowed";
        oNestedException = cStowedException.foCreate(
          oProcess = oProcess,
          uStowedExceptionAddress = uNestedExceptionAddress,
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
          uCPPObjectAddress = uNestedExceptionAddress,
        );
#      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_LMAX:
      else:
        oDataVirtualAllocation = cVirtualAllocation(oProcess.uId, uNestedExceptionAddress);
        uDataOffset = uNestedExceptionAddress - oDataVirtualAllocation.uStartAddress;
        uDataSize = min(0x80, oDataVirtualAllocation.uSize - uDataOffset);
        assert oDataVirtualAllocation.bAllocated, \
            "Cannot read %d bytes stowed exception information from process %d / 0x%X at address 0x%X!" % \
            (uDataSize, oProcess.uId, oProcess.uId, uNestedExceptionAddress);
        auBytes = oDataVirtualAllocation.fauReadBytesForOffsetAndSize(uDataOffset, uDataSize);
        sData = ",".join(["%02X" % uByte for uByte in auBytes]);
        sNestedExceptionTypeId = "Type=0x%08X,Data@0x%08X:[%s]" % \
            (oStowedExceptionInformation.NestedExceptionType, uNestedExceptionAddress, sData);
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
      s0ErrorText = oProcess.fs0ReadNullTerminatedStringForAddress(
        uAddress = oStowedExceptionInformation.ErrorText,
        bUnicode = True,
      );
      oStowedException = cStowedException(
        iCode = oStowedExceptionInformation.ResultCode,
        s0ErrorText = s0ErrorText,
        sNestedExceptionTypeId = sNestedExceptionTypeId,
        oNestedException = oNestedException,
        sWRTLanguageExceptionIUnkownClassName = sWRTLanguageExceptionIUnkownClassName,
      );
    
    return oStowedException;

from cException import cException;
