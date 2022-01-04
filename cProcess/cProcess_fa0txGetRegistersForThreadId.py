from .dttxRelevantRegisters_by_sISA import dttxRelevantRegisters_by_sISA;
from ..mCP437 import fsCP437FromBytesString;

def cProcess_fa0txGetRegistersForThreadId(oProcess, uThreadId):
  oWindowsAPIThread = oProcess.oWindowsAPIProcess.foGetThreadForId(uThreadId);
  d0uRegisterValue_by_sbName = oWindowsAPIThread.fd0uGetRegisterValueByName();
  if d0uRegisterValue_by_sbName is None:
    return None;
  duRegisterValue_by_sbName = d0uRegisterValue_by_sbName;
  atxRegisters = [];
  for (sbRegisterName, uBitSize, bFindDetails) in dttxRelevantRegisters_by_sISA[oProcess.sISA]:
    uRegisterValue = duRegisterValue_by_sbName[sbRegisterName];
    s0Details = None;
    if bFindDetails:
      sb0Symbol = oProcess.fsb0GetSymbolForAddress(uRegisterValue, b"register %s" % sbRegisterName);
      if sb0Symbol:
        s0Details = fsCP437FromBytesString(sb0Symbol);
      else:
        o0HeapManagerData = oProcess.fo0GetHeapManagerDataForAddress(
          uAddress = uRegisterValue,
          bMayNotBeParseable = True, # We do not even know if this is a heap block.
        );
        if o0HeapManagerData:
          (sSizeId, sOffsetId, sOffsetDescription, sSizeDescription) = \
              o0HeapManagerData.ftsGetIdAndDescriptionForAddress(uRegisterValue);
          s0Details = "%s %s" % (sOffsetDescription, sSizeDescription);
    atxRegisters.append((sbRegisterName, uRegisterValue, uBitSize, s0Details));
  return atxRegisters;
