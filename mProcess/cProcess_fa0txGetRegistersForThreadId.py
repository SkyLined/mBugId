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
      s0Details = oProcess.fs0GetDetailsForAddress(uRegisterValue);
    atxRegisters.append((sbRegisterName, uRegisterValue, uBitSize, s0Details));
  return atxRegisters;
