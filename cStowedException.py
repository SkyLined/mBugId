import re;

from mWindowsSDK import (
  STOWED_EXCEPTION_INFORMATION_HEADER,
  STOWED_EXCEPTION_INFORMATION_V1_SIGNATURE,
  STOWED_EXCEPTION_INFORMATION_V132,
  STOWED_EXCEPTION_INFORMATION_V164,
  STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE,
  STOWED_EXCEPTION_INFORMATION_V232,
  STOWED_EXCEPTION_INFORMATION_V264,
  STOWED_EXCEPTION_NESTED_TYPE_CLR,
  STOWED_EXCEPTION_NESTED_TYPE_LEO,
  STOWED_EXCEPTION_NESTED_TYPE_NONE,
  STOWED_EXCEPTION_NESTED_TYPE_STOWED,
  STOWED_EXCEPTION_NESTED_TYPE_WIN32,
);
from mWindowsAPI import cVirtualAllocation;

# local imports are at the end of this file to avoid import loops.

def fsSignature(uSignature):
  return "".join([chr((uSignature >> (uByteIndex * 8)) & 0xFF) for uByteIndex in range(3,-1,-1)]);

class cStowedException(object):
  def __init__(oSelf, \
    iCode,
    u0Address = None,
    p0StackTrace = None, uStackTraceSize = 0,
    s0ErrorText = None,
    s0NestedExceptionTypeId = None,
    o0NestedException = None,
    sb0WRTLanguageExceptionIUnknownClassName = None,
  ):
    oSelf.iCode = iCode; # HRESULT, signed 32-bit integer (negative == error).
    uCode = iCode + (iCode < 0 and (1 << 32) or 0); # Convert to unsigned 32-bit integer.
    oSelf.u0Address = u0Address;
    oSelf.p0StackTrace = p0StackTrace; # dpS {p0StackTrace} L{uStackTraceSize}
    oSelf.uStackTraceSize = uStackTraceSize;
    oSelf.s0ErrorText = s0ErrorText;
    oSelf.s0NestedExceptionTypeId = s0NestedExceptionTypeId;
    oSelf.o0NestedException = o0NestedException;
    oSelf.sb0WRTLanguageExceptionIUnknownClassName = sb0WRTLanguageExceptionIUnknownClassName;
    # Create an exception id that uniquely identifies the exception and a description of the exception.
    o0ErrorDetails = cErrorDetails.fo0GetForCode(uCode);
    if o0ErrorDetails:
      oSelf.sTypeId = o0ErrorDetails.sTypeId;
      oSelf.s0SecurityImpact = o0ErrorDetails.s0SecurityImpact;
      oSelf.sDescription = o0ErrorDetails.sDescription;
    else:
      oSelf.sTypeId = "0x%08X" % uCode;
      oSelf.s0SecurityImpact = "Unknown";
      oSelf.sDescription = "Unknown exception code 0x%08X." % uCode;
    if oSelf.s0ErrorText:
      oSelf.sDescription += " Error: %s" % oSelf.s0ErrorText;
    if s0NestedExceptionTypeId:
      oSelf.sTypeId += ":%s" % (s0NestedExceptionTypeId,);
      if oSelf.o0NestedException:
        oSelf.sTypeId += "(%s)" % (oSelf.o0NestedException.sTypeId,);
        oSelf.sDescription += " Nested %s exception: %s." % \
            (s0NestedExceptionTypeId, oSelf.o0NestedException.sDescription);
        if oSelf.s0SecurityImpact != oSelf.o0NestedException.s0SecurityImpact:
          if oSelf.s0SecurityImpact is None:
            oSelf.s0SecurityImpact = "Nested exception: %s" % \
                oSelf.o0NestedException.s0SecurityImpact;
          elif oSelf.o0NestedException.s0SecurityImpact is not None:
            oSelf.s0SecurityImpact = "%s, nested exception: %s" % \
                (oSelf.s0SecurityImpact, oSelf.o0NestedException.s0SecurityImpact);
    if oSelf.sb0WRTLanguageExceptionIUnknownClassName:
      oSelf.sTypeId += "@%s" % fsCP437FromBytesString(oSelf.sb0WRTLanguageExceptionIUnknownClassName);
      oSelf.sDescription += " WRT Language exception class name: %s." % oSelf.sb0WRTLanguageExceptionIUnknownClassName;
  
  @staticmethod
  def faoCreateForListAddressAndCount(oProcess, uListAddress, uCount):
    a0uStowedExceptionInformationAddresses = oProcess.fa0uReadPointersForAddressAndCount(uListAddress, uCount);
    assert a0uStowedExceptionInformationAddresses, \
        "Cannot read %d stowed exception information pointers from process %d / 0x%X at address 0x%X" % \
        (uCount, oProcess.uId, oProcess.uId, uListAddress);
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
    s0NestedExceptionTypeId = None;
    o0NestedException = None;
    sb0WRTLanguageExceptionIUnknownClassName = None;
    if (
      oStowedExceptionInformationHeader.Signature == STOWED_EXCEPTION_INFORMATION_V2_SIGNATURE
      and oStowedExceptionInformation.NestedExceptionType != STOWED_EXCEPTION_NESTED_TYPE_NONE
    ):
      uNestedExceptionAddress = oStowedExceptionInformation.NestedException.value;
      if oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_WIN32:
        s0NestedExceptionTypeId = "Win32";
        o0NestedException = cException.foCreateFromMemory(
          oProcess = oProcess,
          uExceptionRecordAddress = uNestedExceptionAddress,
        );
      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_STOWED:
        s0NestedExceptionTypeId = "Stowed";
        o0NestedException = cStowedException.foCreate(
          oProcess = oProcess,
          uStowedExceptionAddress = uNestedExceptionAddress,
        );
      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_CLR:
        s0NestedExceptionTypeId = "CLR";
        # TODO: find out how to trigger these so I can find out how to handle them.
      elif oStowedExceptionInformation.NestedExceptionType == STOWED_EXCEPTION_NESTED_TYPE_LEO:
        s0NestedExceptionTypeId = "WRTLanguage";
        # These can be triggered using RoOriginateLanguageException. The "NestedException" contains a pointer to an
        # object that implements IUnknown. Apparently this object "contains all the information necessary recreate it
        # the exception a later point." (https://msdn.microsoft.com/en-us/library/dn302172(v=vs.85).aspx)
        # I have not been able to find more documentation for this, so this is based on reverse engineering.
        sb0WRTLanguageExceptionIUnknownClassName = fsbGetCPPObjectClassNameFromVFTable(
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
        s0NestedExceptionTypeId = "Type=0x%08X,Data@0x%08X:[%s]" % \
            (oStowedExceptionInformation.NestedExceptionType, uNestedExceptionAddress, sData);
    # Handle the two different forms:
    if uExceptionForm == 1:
      oStowedException = cStowedException(
        iCode = oStowedExceptionInformation.ResultCode,
        u0Address = oStowedExceptionInformation.ExceptionAddress,
        p0StackTrace = oStowedExceptionInformation.StackTrace,
        uStackTraceSize = oStowedExceptionInformation.StackTraceWords * oStowedExceptionInformation.StackTraceWordSize,
        s0NestedExceptionTypeId = s0NestedExceptionTypeId,
        o0NestedException = o0NestedException,
        sb0WRTLanguageExceptionIUnknownClassName = sb0WRTLanguageExceptionIUnknownClassName,
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
        s0NestedExceptionTypeId = s0NestedExceptionTypeId,
        o0NestedException = o0NestedException,
        sb0WRTLanguageExceptionIUnknownClassName = sb0WRTLanguageExceptionIUnknownClassName,
      );
    
    return oStowedException;

from .cException import cException;
from .fsbGetCPPObjectClassNameFromVFTable import fsbGetCPPObjectClassNameFromVFTable;
from .cErrorDetails import cErrorDetails;
from .mCP437 import fsCP437FromBytesString;
