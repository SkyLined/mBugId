from ..mCP437 import fsCP437FromBytesString;

def cProcess_fs0GetDetailsForAddress(oProcess, uAddress):
  sb0Symbol = oProcess.fsb0GetSymbolForAddress(uAddress, b"address 0x%X" % uAddress);
  if sb0Symbol:
    return fsCP437FromBytesString(sb0Symbol);
  o0HeapManagerData = oProcess.fo0GetHeapManagerDataForAddressNearHeapBlock(
    uAddressNearHeapBlock = uAddress,
  );
  if o0HeapManagerData:
    (sSizeId, sOffsetId, sOffsetDescription, sSizeDescription) = \
        o0HeapManagerData.ftsGetIdAndDescriptionForAddress(uAddress);
    return "%s %s" % (sOffsetDescription, sSizeDescription);
  return None;