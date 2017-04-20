def fduStructureData(auBytes, atsName_and_uSize):
  duValue_by_sName = {};
  uValueIndex = 0;
  for (sName, uSize) in atsName_and_uSize:
    uValue = 0;
    if uSize:
      for uByteOffset in xrange(uSize):
        uByte = auBytes[uValueIndex + uByteOffset];
        if uByte is None:
          uValue = None;
          break;
        uValue += uByte << (uByteOffset * 8);
    duValue_by_sName[sName] = uValue;
    uValueIndex += uSize;
  return duValue_by_sName;
