from dxBugIdConfig import dxBugIdConfig;

def fsGetNumberDescription(uNumber, sSign = "+"):
  uArchitectureIndependentBugIdBytes = (dxBugIdConfig["uArchitectureIndependentBugIdBits"] or 0) / 8;
  if uArchitectureIndependentBugIdBytes == 0 or uNumber < uArchitectureIndependentBugIdBytes:
    # Architecture independent bug ids are disabled, or the number is too small to require fixing.
    if uNumber < 10:
      return "%d" % uNumber;
    return "0x%X" % uNumber;
  sDescription = "%d*N" % uArchitectureIndependentBugIdBytes;
  uRemainder = uNumber % uArchitectureIndependentBugIdBytes;
  if uRemainder:
    sDescription += sSign + fsGetNumberDescription(uRemainder);
  return sDescription;
