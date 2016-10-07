import re;

def cCdbWrapper_fauGetBytes(oCdbWrapper, uAddress, uSize):
  auBytes = [];
  asBytesOutput = oCdbWrapper.fasSendCommandAndReadOutput("db 0x%X L0x%X" % (uAddress, uSize));
  if not oCdbWrapper.bCdbRunning: return;
  uLineNumber = 0;
  for sLine in asBytesOutput:
    uLineNumber += 1;
    oBytesMatch = re.match(r"^[0-9a-f`]+ ((?:[ \-][\?0-9a-f]{2})+)  .+$", sLine, re.I);
    assert oBytesMatch, \
        "Unexpected output in line %d:\r\n%s" % (uLineNumber, "\r\n".join(asBytesOutput));
    # Convert " xx xx xx-xx xx ..." into ["xx", "xx", "xx", ...]
    asBytes = oBytesMatch.group(1)[1:].replace("-", " ").split(" ");
    for sByte in asBytes:
      if sByte == "??":
        auBytes.append(None);
      else:
        auBytes.append(int(sByte, 16));
  assert len(auBytes) == uSize, \
      "Internal error: got %d bytes, but expected %d\r\n%s" % (len(auBytes), uSize, "\r\n".join(asBytesOutput));
  return auBytes;