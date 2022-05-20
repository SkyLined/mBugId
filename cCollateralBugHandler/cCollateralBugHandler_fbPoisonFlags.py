
def cCollateralBugHandler_fbPoisonFlags(
  oSelf,
  oCdbWrapper,
  oProcess,
  oThread,
  sInstruction,
  duPoisonedRegisterValue_by_sbName,
  u0PointerSizedOriginalValue,
):
  # This instruction will affect flags, so we'll read bits from the poisoned values to use as flags.
  asbFlagNames = [b"of", b"sf", b"zf", b"af", b"pf", b"cf"];
  # Accumulate the flag bits into a single value
  uCurrentFlagsValue = 0;
  for uIndex in range(len(asbFlagNames)):
    sbFlagName = asbFlagNames[uIndex];
    u0FlagValue = oThread.fu0GetRegister(sbFlagName);
    if u0FlagValue is None:
      oCdbWrapper.fFireCallbacks(
      "Bug cannot be ignored", 
      "cannot read current flag %s value" % repr(sbFlagName)[1:],
      );
      return False;
    uCurrentFlagsValue += u0FlagValue << uIndex;
  # Get a poisoned value to replace the flags:
  uPoisonedFlagsValue = oSelf.fuGetPoisonedValue(
    oProcess = oProcess,
    oWindowsAPIThread = oProcess.foGetWindowsAPIThreadForId(oThread.uId),
    sDestination = "flags(%s)" % ", ".join(str(sbFlagName, "ascii", "strict") for sbFlagName in asbFlagNames),
    sInstruction = sInstruction,
    i0CurrentValue = uCurrentFlagsValue,
    uBits = len(asbFlagNames),
    u0PointerSizedOriginalValue = u0PointerSizedOriginalValue,
  );
  # Set the flags in the dict.
  for uIndex in range(len(asbFlagNames)):
    sFlagName = asbFlagNames[uIndex];
    duPoisonedRegisterValue_by_sbName[sFlagName] = (uPoisonedFlagsValue >> uIndex) & 1;
  return True;