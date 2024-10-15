import re;

from mWindowsSDK import *;

from .cStowedException import cStowedException;
from .cErrorDetails import cErrorDetails;
from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from .mCP437 import fsCP437FromBytesString;

grb_exr_ExceptionOutputLine = re.compile(
  rb"^\s*"                              #   optional whitespace
  rb"([A-Za-z]+)"                       # * name
  rb"(?:"                               #   optional {
    rb"\["                              #     "["
    rb"(\d+)"                           # *   index
    rb"\]"                              #     "["
  rb")?"                                #   }
  rb": "                                #   ": "
  rb"([0-9a-f`]+)"                      # * value
  rb"(?:"                               #   optional {
    rb" \("                              #    " ("
    rb"(.+)"                            # *   symbol_or_code_description
    rb"\)"                              #     ")"
  rb")?"                                #   }
  rb"\s*$"                              # optional whitespace
);

class cException(object):
  @classmethod
  def foCreateFromMemory(cException, oProcess, uExceptionRecordAddress):
    return cException(oProcess, uExceptionRecordAddress, False);
    
  @classmethod
  def foCreateForLastExceptionInProcess(cException, oProcess, uExpectedCode, bApplicationCannotHandleException):
    return cException(oProcess, None, bApplicationCannotHandleException);
    assert cException.uCode == uExpectedCode, \
        "Exception record has an unexpected ExceptionCode value (0x%08X vs 0x%08X)" % \
        (cException.uCode, uExpectedCode);
  
  @classmethod
  def __init__(oSelf, oProcess, u0ExceptionRecordAddress, bApplicationCannotHandleException):
    oSelf.bApplicationCannotHandleException = bApplicationCannotHandleException;
    asbExceptionRecord = oProcess.fasbExecuteCdbCommand(
      sbCommand = b".exr %s;" % (u0ExceptionRecordAddress is None and b"-1" or b"0x%X" % u0ExceptionRecordAddress),
      sb0Comment = b"Get exception record",
      bOutputIsInformative = True,
      bRetryOnTruncatedOutput = True,
    );
    oSelf.asCdbLines = asbExceptionRecord;
    # Sample output:
    # |ExceptionAddress: 00007ff6b0f81204 (Tests_x64!fJMP+0x0000000000000004)
    # |   ExceptionCode: c0000005 (Access violation)
    # |  ExceptionFlags: 00000000
    # |NumberParameters: 2
    # |   Parameter[0]: 0000000000000000
    # |   Parameter[1]: ffffffffffffffff
    # |Attempt to read from address ffffffffffffffff
    u0InstructionPointer = None; # Must be initialized below!
    sb0AddressSymbol = None; 
    u0Code = None; # Must be initialized below!
    oSelf.sb0CodeDescription = None;
    u0Flags = None; # Must be initialized below!
    u0ParameterCount = None; # Must be initialized below!
    oSelf.sb0Details = None; # May or may not be set below.
    oSelf.auParameters = [];
    uParameterIndex = 0;
    for uLineIndex in range(len(asbExceptionRecord)):
      sbLine = asbExceptionRecord[uLineIndex];
      oNameValueMatch = grb_exr_ExceptionOutputLine.match(sbLine);
      if oNameValueMatch:
        sbName, sb0ParameterIndex, sbValue, sb0SymbolOrCodeDescription = oNameValueMatch.groups();
        uValue = fu0ValueFromCdbHexOutput(sbValue);
        if sbName == b"ExceptionAddress":
          assert u0InstructionPointer is None, \
              "Cannot have two values for %s: %s" % (repr(sbName), repr(asbExceptionRecord));
          u0InstructionPointer = uValue;
          sb0AddressSymbol = sb0SymbolOrCodeDescription;
        elif sbName == b"ExceptionCode":
          assert u0Code is None, \
              "Cannot have two values for %s: %s" % (repr(sbName), repr(asbExceptionRecord));
          u0Code = uValue;
          oSelf.sb0CodeDescription = sb0SymbolOrCodeDescription;
        elif sbName == b"ExceptionFlags":
          assert u0Flags is None, \
              "Cannot have two values for %s: %s" % (repr(sbName), repr(asbExceptionRecord));
          u0Flags = uValue;
        elif sbName == b"NumberParameters":
          assert u0ParameterCount is None, \
              "Cannot have two values for %s: %s" % (repr(sbName), repr(asbExceptionRecord));
          u0ParameterCount = uValue;
        elif sbName == b"Parameter":
          assert u0ParameterCount is not None, \
              "Unexpected parameter before NumberParameters value\r\n%s" % \
              "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord);
          assert fu0ValueFromCdbHexOutput(sb0ParameterIndex) == uParameterIndex, \
              "Unexpected parameter #0x%s vs 0x%X\r\n%s" % \
              (sb0ParameterIndex, uParameterIndex, "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord));
          oSelf.auParameters.append(uValue);
          uParameterIndex += 1;
        else:
          raise AssertionError("Unknown exception record value name %s:\r\n%s" % (repr(sbName), repr(asbExceptionRecord)));
      else:
        assert uLineIndex == len(asbExceptionRecord) - 1, \
            "Unrecognized exception record line %s: %s" % \
            (sbLine, "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord));
        oSelf.sb0Details = asbExceptionRecord[-1];
    
    assert u0InstructionPointer is not None, \
        "Exception record is missing an ExceptionAddress value\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord);
    oSelf.uInstructionPointer = u0InstructionPointer;
    assert u0Code is not None, \
        "Exception record is missing an ExceptionCode value\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord);
    oSelf.uCode = u0Code;
    assert u0Flags is not None, \
        "Exception record is missing an ExceptionFlags value\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord);
    oSelf.uFlags = u0Flags;
    assert u0ParameterCount is not None, \
        "Exception record is missing an NumberParameters value\r\n%s" % \
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord);
    assert u0ParameterCount == len(oSelf.auParameters), \
        "Expected %d parameters but found %d\r\n%s" % (
          u0ParameterCount,
          len(oSelf.auParameters),
          "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbExceptionRecord)
        );
    # Now get a preliminary exception id that identifies the type of exception based on the exception code, as well as
    # preliminary security impact.
    o0ErrorDetails = cErrorDetails.fo0GetForCode(oSelf.uCode);
    if o0ErrorDetails:
      oSelf.sTypeId = o0ErrorDetails.sTypeId;
      oSelf.sDescription = o0ErrorDetails.sDescription;
      oSelf.s0SecurityImpact = o0ErrorDetails.s0SecurityImpact;
    else:
      oSelf.sTypeId = "0x%08X" % oSelf.uCode;
      oSelf.sDescription = "Unknown exception code 0x%08X%s" % (
        oSelf.uCode,
        (" (%s)" % fsCP437FromBytesString(oSelf.sb0CodeDescription)) if oSelf.sb0CodeDescription else ""
      );
      oSelf.s0SecurityImpact = "Unknown";
    
    if sb0AddressSymbol:
      (
        oSelf.u0Address,
        oSelf.s0UnloadedModuleFileName, oSelf.o0Module, oSelf.u0ModuleOffset,
        oSelf.o0Function, oSelf.i0OffsetFromStartOfFunction
      ) = oProcess.ftxSplitSymbolOrAddress(sb0AddressSymbol);
    else:
      oSelf.u0Address = oSelf.uInstructionPointer;
      oSelf.s0UnloadedModuleFileName = None;
      oSelf.o0Module = None;
      oSelf.u0ModuleOffset = None;
      oSelf.o0Function = None;
      oSelf.i0OffsetFromStartOfFunction = None;
    
    # Compare stack with exception information
    
    #### Work-around for a cdb bug ###############################################################################
    # cdb appears to assume most breakpoints are triggered by an int3 instruction and sets the exception address
    # to the instruction that would follow the int3. Since int3 is a one byte instruction, the exception address
    # will be off-by-one. We will try fix this by decreasing the instruction pointer.
    if oSelf.uCode in [STATUS_WX86_BREAKPOINT, STATUS_BREAKPOINT]:
      if oSelf.u0Address is not None:
        oSelf.uInstructionPointer -= 1;
        oSelf.u0Address -= 1;
      elif oSelf.u0ModuleOffset is not None:
        if oSelf.u0ModuleOffset > 0:
          oSelf.uInstructionPointer -= 1;
          oSelf.u0ModuleOffset -= 1;
      elif oSelf.i0OffsetFromStartOfFunction is not None:
        if oSelf.i0OffsetFromStartOfFunction > 0: # Only fix if it looks like it would require fixing
          oSelf.i0OffsetFromStartOfFunction -= 1;
      else:
        raise AssertionError("The exception record appears to have no address or offet to adjust.\r\n%s" % \
            b"\r\n".join(oSelf.asCdbLines));
