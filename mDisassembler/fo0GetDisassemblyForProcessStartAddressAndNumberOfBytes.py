from mNotProvided import fAssertTypes;

from .fo0GetDisassemblyFromCdbOutput import fo0GetDisassemblyFromCdbOutput;

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
  asbDisassemblyOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b"u 0x%X 0x%X" % (uStartAddress, uStartAddress + uNumberOfBytes), 
    sb0Comment = b"Disassemble %d bytes at %d" % (uNumberOfBytes, uStartAddress),
  );
  return fo0GetDisassemblyFromCdbOutput(asbDisassemblyOutput);

