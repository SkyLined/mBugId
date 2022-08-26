from mNotProvided import fAssertTypes;

from mWindowsAPI import fsHexNumber;
from .fo0GetDisassemblyForProcessAndCdbCommand import fo0GetDisassemblyForProcessAndCdbCommand;

def fo0GetDisassemblyForProcessStartAddressAndNumberOfBytes(
  oProcess,
  uStartAddress,
  uNumberOfBytes,
):
  fAssertTypes({
    "uStartAddress": (uStartAddress, int),
    "uNumberOfBytes": (uNumberOfBytes, int),
  });
  assert 0 <= uNumberOfBytes < 0x1000, \
      "Request to disassemble %d bytes seems a little excessive!" % uNumberOfBytes;
  return fo0GetDisassemblyForProcessAndCdbCommand(
    oProcess,
    sbCommand = b"u 0x%X 0x%X" % (uStartAddress, uStartAddress + uNumberOfBytes), 
    sbComment = b"Disassemble %d bytes at %s" % (uNumberOfBytes, bytes(fsHexNumber(uStartAddress), "ascii", "strict")),
  );

