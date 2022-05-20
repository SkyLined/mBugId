def cCollateralBugHandler_fbPoisonRegister(
  oSelf,
  oProcess,
  oThread,
  sInstruction,
  duPoisonedRegisterValue_by_sbName,
  u0PointerSizedOriginalValue,
  sbRegisterName,
  uSizeInBits,
):
  uPoisonValue = oSelf.fuGetPoisonedValue(
    oProcess = oProcess,
    oWindowsAPIThread = oProcess.foGetWindowsAPIThreadForId(oThread.uId),
    sDestination = str(b"register %s" % sbRegisterName, "ascii", "strict"),
    sInstruction = sInstruction,
    i0CurrentValue = oThread.fu0GetRegister(sbRegisterName),
    uBits = uSizeInBits,
    u0PointerSizedOriginalValue = u0PointerSizedOriginalValue,
  );
#    print "Faked read %d bits (0x%X) into %d bits %s" % (uSourceSize, uPoisonValue, uDestinationSizeInBits, sbRegisterName);
  duPoisonedRegisterValue_by_sbName[sbRegisterName] = uPoisonValue;
  return True;