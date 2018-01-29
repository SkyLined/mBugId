from fbIgnoreAccessViolationException import fbIgnoreAccessViolationException;
from ..fsGetNumberDescription import fsGetNumberDescription;

gddtsDetails_uSpecialAddress_sISA = {
  # There are a number of values that are very close to eachother, and because an offset is likely to be added when
  # reading using a pointer, having all of them here does not offer extra information. So, I've limited it to values
  # that are sufficiently far away from eachother to be recognisable after adding offsets.
  "x86": {              # Id                      Description                                           Security impact
            # https://en.wikipedia.org/wiki/Magic_number_(programming)#Magic_debug_values
            0xA0A0A0A0: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary", "Potentially exploitable security issue"),
            # https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
            0xABCDAAAA: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a heap block header", "Potentially exploitable security issue"),
            0xABCDBBBB: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a full heap block header", "Potentially exploitable security issue"),
            0xBBADBEEF: ("Assertion",             "an address that indicates an assertion has failed",  None),
            0xBAADF00D: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            0xCCCCCCCC: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            0xC0C0C0C0: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            0xCDCDCDCD: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            0xD0D0D0D0: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            # https://msdn.microsoft.com/en-us/library/ms220938(v=vs.90).aspx
            0xDCBAAAAA: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a heap block header", "Potentially exploitable security issue"),
            0xDCBABBBB: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary in a full heap block header", "Potentially exploitable security issue"),
            0xDDDDDDDD: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
            0xE0E0E0E0: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),             
            # https://hg.mozilla.org/releases/mozilla-beta/rev/8008235a2429
            0xE4E4E4E4: ("PoisonUninitialized",   "a pointer that was not initialized",                 "Potentially exploitable security issue"),
            0xE5E5E5E5: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
            0xF0090100: ("Poison",                "a pointer read from poisoned memory",                "Potentially exploitable security issue"),
            0xF0DE7FFF: ("Poison",                "a pointer read from poisoned memory",                "Potentially exploitable security issue"),
            0xF0F0F0F0: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
            0xFDFDFDFD: ("PoisonOOB",             "a pointer read from an out-of-bounds memory canary", "Potentially exploitable security issue"),
            0xFEEEFEEE: ("PoisonFree",            "a pointer read from poisoned freed memory",          "Potentially exploitable security issue"),
  },
  "x64": {              # Id                      Description                                           Security impact
    # Note that on x64, addresses with the most significant bit set cannot be allocated in user-land. Since BugId is expected to analyze only user-land
    # applications, accessing such an address is not expected to be an exploitable security issue.
    0xBAADF00DBAADF00D: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xCCCCCCCCCCCCCCCC: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xC0C0C0C0C0C0C0C0: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xCDCDCDCDCDCDCDCD: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xD0D0D0D0D0D0D0D0: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xDDDDDDDDDDDDDDDD: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
    0xF0F0F0F0F0F0F0F0: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
    0xF0DE7FFFF0DE7FFF: ("Poison",                "a pointer read from poisoned memory",                None),
    0xF0090100F0090100: ("Poison",                "a pointer read from poisoned memory",                None),
    0xFEEEFEEEFEEEFEEE: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
    # https://hg.mozilla.org/releases/mozilla-beta/rev/8008235a2429
    0xE4E4E4E4E4E4E4E4: ("PoisonUninitialized",   "a pointer that was not initialized",                 None),
    0xE5E5E5E5E5E5E5E5: ("PoisonFree",            "a pointer read from poisoned freed memory",          None),
  },
};

def fbUpdateReportForSpecialPointer(
  oCdbWrapper, oBugReport, oProcess, sViolationTypeId, uAccessViolationAddress, sViolationTypeDescription, oVirtualAllocation
):
  dtsDetails_uSpecialAddress = gddtsDetails_uSpecialAddress_sISA[oProcess.sISA];
  for (uSpecialAddress, (sSpecialAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
    iOffset = uAccessViolationAddress - uSpecialAddress;
    if iOffset != 0:
      uOverflow = {"x86": 1 << 32, "x64": 1 << 64}[oProcess.sISA];
      if iOffset > dxConfig["uMaxAddressOffset"]: # Maybe this is wrapping:
        iOffset -= uOverflow;
      elif iOffset < -dxConfig["uMaxAddressOffset"]: # Maybe this is wrapping:
        iOffset += uOverflow;
    uOffset = abs(iOffset);
    if uOffset <= dxConfig["uMaxAddressOffset"]:
      sSign = iOffset < 0 and "-" or "+";
      sOffset = iOffset != 0 and "%s%s" % (sSign, fsGetNumberDescription(uOffset, sSign)) or "";
      oBugReport.sBugTypeId = "AV%s@%s%s" % (sViolationTypeId, sSpecialAddressId, sOffset);
      oBugReport.sBugDescription = "Access violation while %s memory at 0x%X using %s." % \
        (sViolationTypeDescription, uAccessViolationAddress, sAddressDescription);
      oBugReport.sSecurityImpact = sSecurityImpact;
      oCdbWrapper.oCollateralBugHandler.fSetIgnoreExceptionFunction(lambda oCollateralBugHandler:
        fbIgnoreAccessViolationException(oCollateralBugHandler, oCdbWrapper, oProcess.uId, sViolationTypeId)
      );
      return True;
  return False;

