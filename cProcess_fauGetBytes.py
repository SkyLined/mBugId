import re;
from dxConfig import dxConfig;

def cProcess_fauGetBytes(oProcess, uAddress, uSize, sComment):
  assert uSize <= dxConfig["uMaxMemoryDumpSize"], \
      "Attempt to dump %d/0x%X bytes but the max is %d/0x%X" % (uSize, uSize, dxConfig["uMaxMemoryDumpSize"], dxConfig["uMaxMemoryDumpSize"]);
  auBytes = [];
  assert ";" not in sComment, \
      "Comments cannot have a semi-colon: %s" % repr(sComment);
  asCommandOutput = oProcess.fasExecuteCdbCommand(
    sCommand = "db /c20 0x%X L0x%X;" % (uAddress, uSize),
    sComment = sComment,
    bRetryOnTruncatedOutput = True,
  );
  uLineNumber = 0;
  for sLine in asCommandOutput:
    uLineNumber += 1;
    oBytesMatch = re.match(r"^[0-9a-f`]+ ((?:[ \-][\?0-9a-f]{2})+)  .+$", sLine, re.I);
    assert oBytesMatch, \
        "Unexpected output in line %d:\r\n%s" % (uLineNumber, "\r\n".join(asCommandOutput));
    # Convert " xx xx xx-xx xx ..." into ["xx", "xx", "xx", ...]
    asBytes = oBytesMatch.group(1)[1:].replace("-", " ").split(" ");
    for sByte in asBytes:
      if sByte == "??":
        auBytes.append(None);
      else:
        auBytes.append(int(sByte, 16));
  assert len(auBytes) == uSize, \
      "Internal error: expected %d bytes, got %s\r\n%s" % (uSize, repr(auBytes), "\r\n".join(asCommandOutput));
  return auBytes;
