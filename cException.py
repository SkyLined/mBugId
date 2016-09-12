import re;
from cStowedException import cStowedException;
from dtsTypeId_and_sSecurityImpact_by_uExceptionCode import dtsTypeId_and_sSecurityImpact_by_uExceptionCode;
from dxBugIdConfig import dxBugIdConfig;
from NTSTATUS import *;

def fsAddressData(oStackFrameOrException):
  return "ip=0x%X addr=%s mod=%s,%s%s func=%s%s" % (
    oStackFrameOrException.uInstructionPointer,
    oStackFrameOrException.uAddress is None and "-" or "0x%X" % oStackFrameOrException.uAddress,
    oStackFrameOrException.sUnloadedModuleFileName or "-",
    oStackFrameOrException.oModule and "%s@%s" % (
      oStackFrameOrException.oModule.sBinaryName,
      oStackFrameOrException.oModule.uStartAddress and "0x%X" % oStackFrameOrException.oModule.uStartAddress or "?"
    ) or "-",
    oStackFrameOrException.uModuleOffset and "%s0x%X" % (
        oStackFrameOrException.uModuleOffset < 0 and "-" or "+",
        abs(oStackFrameOrException.uModuleOffset)
    ) or "",
    oStackFrameOrException.oFunction and oStackFrameOrException.oFunction.sSymbol or "-",
    oStackFrameOrException.uFunctionOffset and "%s0x%X" % (
        oStackFrameOrException.uFunctionOffset < 0 and "-" or "+",
        abs(oStackFrameOrException.uFunctionOffset)
    ) or "",
  )


class cException(object):
  def __init__(oException, asCdbLines, uCode, sCodeDescription):
    oException.asCdbLines = asCdbLines; # This is here merely to be able to debug issues - it is not used.
    oException.uCode = uCode;
    oException.sCodeDescription = sCodeDescription;
    
    oException.uAddress = None;
    oException.sAddressSymbol = None; # See below
    oException.sUnloadedModuleFileName = None;
    oException.oModule = None;
    oException.uModuleOffset = None;
    oException.oFunction = None;
    oException.uFunctionOffset = None;
    
    oException.uFlags = None;
    oException.auParameters = None;
    oException.sDetails = None;
    oException.sTypeId = None;
    oException.sDescription = None;
    oException.sSecurityImpact = None;
  
  @classmethod
  def foCreate(cException, oCdbWrapper, uCode, sCodeDescription, oStack):
    asExceptionRecord = oCdbWrapper.fasSendCommandAndReadOutput(
      ".exr -1; $$ Get exception record",
      bOutputIsInformative = True,
    );
    if not oCdbWrapper.bCdbRunning: return None;
    oException = cException(asExceptionRecord, uCode, sCodeDescription);
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
          assert uValue == uCode, \
              "Exception record has an unexpected ExceptionCode value (0x%08X vs 0x%08X)\r\n%s" % \
              (uValue, uCode, "\r\n".join(asExceptionRecord));
          assert sDetails is None or sDetails == sCodeDescription, \
              "Exception record has an unexpected ExceptionCode description (%s vs %s)\r\n%s" % \
              (repr(sDetails), repr(sCodeDescription), "\r\n".join(asExceptionRecord));
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
    if oException.uCode in dtsTypeId_and_sSecurityImpact_by_uExceptionCode:
      oException.sTypeId, oException.sSecurityImpact = dtsTypeId_and_sSecurityImpact_by_uExceptionCode[oException.uCode];
    else:
      oException.sTypeId = "0x%08X" % oException.uCode;
      oException.sSecurityImpact = "Unknown";
    # Save the description of the issue
    oException.sDescription = "%s (code 0x%08X)" % (sCodeDescription, uCode);

    # Compare stack with exception information
    if oException.sAddressSymbol:
      doModules_by_sCdbId = oCdbWrapper.fdoGetModulesByCdbIdForCurrentProcess();
      (
        oException.uAddress,
        oException.sUnloadedModuleFileName, oException.oModule, oException.uModuleOffset,
        oException.oFunction, oException.uFunctionOffset
      ) = oCdbWrapper.ftxSplitSymbolOrAddress(oException.sAddressSymbol, doModules_by_sCdbId);
      sCdbLine = oException.sAddressSymbol;
      if oException.uCode == STATUS_BREAKPOINT and oException.oFunction and oException.oFunction.sName == "ntdll.dll!DbgBreakPoint":
        # This breakpoint most likely got inserted into the process by cdb. There will be no trace of it in the stack,
        # so do not try to check that exception information matches the first stack frame.
        return None;
    else:
      oException.uAddress = oException.uInstructionPointer;
      sCdbLine = sCdbExceptionAddress; # "address (symbol)" from "ExceptionAddress:" (Note: will never be None)
    if not oStack.aoFrames:
      # Failed to get stack, use information from exception and the current return adderss to reconstruct the top frame.
      uReturnAddress = oCdbWrapper.fuGetValue("@$ra");
      if not oCdbWrapper.bCdbRunning: return;
      oStack.fCreateAndAddStackFrame(
        uNumber = 0,
        sCdbLine = sCdbLine,
        uInstructionPointer = oException.uInstructionPointer,
        uReturnAddress = uReturnAddress,
        uAddress = oException.uAddress,
        sUnloadedModuleFileName = oException.sUnloadedModuleFileName,
        oModule = oException.oModule, uModuleOffset = oException.uModuleOffset,
        oFunction = oException.oFunction, uFunctionOffset = oException.uFunctionOffset,
        # No source information.
      );
    else:
      if oException.uCode == STATUS_WAKE_SYSTEM_DEBUGGER:
        # This exception does not happen in a particular part of the code, and the exception address is therefore 0.
        # Do not try to find this address on the stack.
        pass;
      else:
        #### Work-around for a cdb bug ###############################################################################
        # cdb appears to assume all breakpoints are triggered by an int3 instruction and sets the exception address
        # to the instruction that would follow the int3. Since int3 is a one byte instruction, the exception address
        # will be off-by-one.
        bExceptionOffByOne = oException.uCode in [STATUS_WX86_BREAKPOINT, STATUS_BREAKPOINT]
        if bExceptionOffByOne:
          oException.uInstructionPointer -= 1;
          if oException.uAddress is not None:
            oException.uAddress -= 1;
          elif oException.uModuleOffset is not None:
            oException.uModuleOffset -= 1;
          elif oException.uFunctionOffset is not None:
            oException.uFunctionOffset -= 1;
          else:
            raise AssertionError("The exception record appears to have no address or offet to adjust.\r\n%s" % oException.asExceptionRecord);
        # Under all circumstances one expects there to be a stack frame for the exception (i.e. the stack frame has
        # the same uInstructionPointer as the exception). There may be stack frames above it that were used to trigger
        # the exception ((e.g. ntdll!RaiseException) but these are not relevant to the bug and can be hidden.
        # We need to special case int3 breakpoints: the exception happens at the int3 instruction, but the first stack
        # frame should point to the instruction immediately following it (one byte higher).
        bInt3 = bExceptionOffByOne and oException.uInstructionPointer + 1 == oStack.aoFrames[0].uInstructionPointer
        if not bInt3:
          for oFrame in oStack.aoFrames:
            if oFrame.uInstructionPointer == oException.uInstructionPointer:
              break;
            oFrame.bIsHidden = True;
          else:
            raise AssertionError("The %sexception address was not found on the stack\r\n%s\r\n---\r\n%s" % (
              bOffByOne and "adjusted " or "",
              fsAddressData(oException),
              "\r\n".join([fsAddressData(oFrame) for oFrame in oStack.aoFrames])
            ));
    return oException;