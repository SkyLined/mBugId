import re;
from cStack import cStack;
from cStowedException import cStowedException;
from cWindowsStatusOrError import cWindowsStatusOrError;
from mWindowsAPI.mDefines import *;

class cException(object):
  def __init__(oException, asCdbLines, uCode, sCodeDescription, bApplicationCannotHandleException):
    oException.asCdbLines = asCdbLines; # This is here merely to be able to debug issues - it is not used.
    oException.uCode = uCode;
    oException.sCodeDescription = sCodeDescription;
    oException.bApplicationCannotHandleException = bApplicationCannotHandleException;
    
    oException.uAddress = None;
    oException.sAddressSymbol = None; # See below
    oException.sUnloadedModuleFileName = None;
    oException.oModule = None;
    oException.uModuleOffset = None;
    oException.oFunction = None;
    oException.iFunctionOffset = None;
    
    oException.uFlags = None;
    oException.auParameters = None;
    oException.sDetails = None;
    oException.sTypeId = None;
    oException.sDescription = None;
    oException.sSecurityImpact = None;
  
  @classmethod
  def foCreateFromMemory(cException, oProcess, uExceptionRecordAddress):
    return cException.foCreateHelper(oProcess,
      uExceptionRecordAddress = uExceptionRecordAddress,
      bApplicationCannotHandleException = False,
    );
    
  @classmethod
  def foCreate(cException, oProcess, uCode, sCodeDescription, bApplicationCannotHandleException):
    return cException.foCreateHelper(oProcess, 
      uCode = uCode,
      sCodeDescription = sCodeDescription,
      bApplicationCannotHandleException = bApplicationCannotHandleException,
    );

  @classmethod
  def foCreateHelper(cException, oProcess,
      # Either
        uExceptionRecordAddress = None,
      # Or
        uCode = None,
        sCodeDescription = None,
      # Always
      bApplicationCannotHandleException = None
  ):
    assert bApplicationCannotHandleException is not None, \
        "bApplicationCannotHandleException is required!";
    asExceptionRecord = oProcess.fasExecuteCdbCommand(
      sCommand = ".exr %s;" % (uExceptionRecordAddress is None and "-1" or "0x%X" % uExceptionRecordAddress),
      sComment = "Get exception record",
      bOutputIsInformative = True,
      bRetryOnTruncatedOutput = True,
    );
    oException = cException(asExceptionRecord, uCode, sCodeDescription, bApplicationCannotHandleException);
    # Sample output:
    # |ExceptionAddress: 00007ff6b0f81204 (Tests_x64!fJMP+0x0000000000000004)
    # |   ExceptionCode: c0000005 (Access violation)
    # |  ExceptionFlags: 00000000
    # |NumberParameters: 2
    # |   Parameter[0]: 0000000000000000
    # |   Parameter[1]: ffffffffffffffff
    # |Attempt to read from address ffffffffffffffff
    uParameterCount = None;
    uParameterIndex = None;
    sCdbExceptionAddress = None;
    for sLine in asExceptionRecord:
      oNameValueMatch = re.match(r"^\s*%s\s*$" % (
        r"(\w+)(?:\[(\d+)\])?\:\s+"     # (name) optional{ "[" (index) "]" } ":" whitespace
        r"([0-9A-F`]+)"                 # (value)
        r"(?:\s+\((.*)\))?"             # optional{ whitespace "(" (symbol || description) ")" }
      ), sLine, re.I);
      if oNameValueMatch:
        sName, sIndex, sValue, sDetails = oNameValueMatch.groups();
        uValue = long(sValue.replace("`", ""), 16);
        if sName == "ExceptionAddress":
          oException.uInstructionPointer = uValue;
          sCdbExceptionAddress = sValue + (sDetails and " (%s)" % sDetails or "");
          oException.sAddressSymbol = sDetails;
        elif sName == "ExceptionCode":
          if uCode:
            assert uValue == uCode, \
                "Exception record has an unexpected ExceptionCode value (0x%08X vs 0x%08X)\r\n%s" % \
                (uValue, uCode, "\r\n".join(asExceptionRecord));
          else:
            oException.uCode = uValue;
          if sCodeDescription:
            assert sDetails is None or sDetails == sCodeDescription, \
                "Exception record has an unexpected ExceptionCode description (%s vs %s)\r\n%s" % \
                (repr(sDetails), repr(sCodeDescription), "\r\n".join(asExceptionRecord));
          else:
            oException.sCodeDescription = sDetails;
        elif sName == "ExceptionFlags":
          oException.uFlags = uValue;
        elif sName == "NumberParameters":
          uParameterCount = uValue;
          uParameterIndex = 0;
          oException.auParameters = [];
        elif sName == "Parameter":
          assert long(sIndex, 16) == uParameterIndex, \
              "Unexpected parameter #0x%s vs 0x%X\r\n%s" % (sIndex, uParameterIndex, "\r\n".join(asExceptionRecord));
          oException.auParameters.append(uValue);
          uParameterIndex += 1;
        else:
          raise AssertionError("Unknown exception record value %s\r\n%s" % (sLine, "\r\n".join(asExceptionRecord)));
      elif oException.sDetails is None:
        oException.sDetails = sLine;
      else:
        raise AssertionError("Superfluous exception record line %s\r\n%s" % (sLine, "\r\n".join(asExceptionRecord)));
    assert oException.uInstructionPointer is not None, \
        "Exception record is missing an ExceptionAddress value\r\n%s" % "\r\n".join(asExceptionRecord);
    assert oException.uFlags is not None, \
        "Exception record is missing an ExceptionFlags value\r\n%s" % "\r\n".join(asExceptionRecord);
    assert uParameterCount is not None, \
        "Exception record is missing an NumberParameters value\r\n%s" % "\r\n".join(asExceptionRecord);
    assert uParameterCount == len(oException.auParameters), \
        "Unexpected number of parameters (%d vs %d)" % (len(oException.auParameters), uParameterCount);
    # Now get a preliminary exception id that identifies the type of exception based on the exception code, as well as
    # preliminary security impact.
    oWindowsStatusOrError = cWindowsStatusOrError.foGetForCode(uCode);
    if oWindowsStatusOrError:
      oException.sTypeId = oWindowsStatusOrError.sTypeId;
      oException.sSecurityImpact = oWindowsStatusOrError.sSecurityImpact;
      oException.sDescription = oWindowsStatusOrError.sDescription;
    else:
      oException.sTypeId = "0x%08X" % uCode;
      oException.sSecurityImpact = "Unknown";
      if sCodeDescription:
        oException.sDescription = "Unknown exception code 0x%08X (%s)" % (uCode, sCodeDescription);
      else:
        oException.sDescription = "Unknown exception code 0x%08X" % uCode;

    # Compare stack with exception information
    if oException.sAddressSymbol:
      (
        oException.uAddress,
        oException.sUnloadedModuleFileName, oException.oModule, oException.uModuleOffset,
        oException.oFunction, oException.iFunctionOffset
      ) = oProcess.ftxSplitSymbolOrAddress(oException.sAddressSymbol);
      sCdbSymbolOrAddress = oException.sAddressSymbol;
      if oException.uCode == STATUS_BREAKPOINT and oException.oFunction and oException.oFunction.sName == "ntdll.dll!DbgBreakPoint":
        # This breakpoint most likely got inserted into the process by cdb. There will be no trace of it in the stack,
        # so do not try to check that exception information matches the first stack frame.
        return None;
    else:
      oException.uAddress = oException.uInstructionPointer;
      sCdbSymbolOrAddress = sCdbExceptionAddress; # "address (symbol)" from "ExceptionAddress:" (Note: will never be None)
    
    #### Work-around for a cdb bug ###############################################################################
    # cdb appears to assume all breakpoints are triggered by an int3 instruction and sets the exception address
    # to the instruction that would follow the int3. Since int3 is a one byte instruction, the exception address
    # will be off-by-one.
    if oException.uCode in [STATUS_WX86_BREAKPOINT, STATUS_BREAKPOINT]:
      oException.uInstructionPointer -= 1;
      if oException.uAddress is not None:
        oException.uAddress -= 1;
      elif oException.uModuleOffset is not None:
        oException.uModuleOffset -= 1;
      elif oException.iFunctionOffset is not None:
        oException.iFunctionOffset -= 1;
      else:
        raise AssertionError("The exception record appears to have no address or offet to adjust.\r\n%s" % oException.asExceptionRecord);
    return oException;