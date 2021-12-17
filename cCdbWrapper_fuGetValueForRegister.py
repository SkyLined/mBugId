from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from .mCP437 import fsCP437FromBytesString;

def cCdbWrapper_fuGetValueForRegister(oCdbWrapper, sbRegister, sb0Comment):
  # This is a register or pseudo-register: it's much faster to get these using the "r" command than printing them
  # as is done for other values:
  asbCommandOutput = oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b"r @%s;" % sbRegister,
    sb0Comment = sb0Comment,
  );
  assert len(asbCommandOutput) == 1, \
      "Expected exactly one line in \"r\" command output:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCommandOutput);
  asbRegisterAndValueResult = asbCommandOutput[0].split(b"=", 1);
  assert len(asbRegisterAndValueResult) == 2, \
      "Missing \"=\" in result:\r\n%s" % \
      "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCommandOutput);
  sbRegisterResult, sbValue = asbRegisterAndValueResult;
  assert sbRegisterResult.lower() == sbRegister.lower(), \
      "Expected result to start with %s, not %s\r\n%s" % (
        repr(sbRegister.lower() + "="),
        repr(sbRegisterResult + "="), 
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCommandOutput)
      );
  try:
    return fu0ValueFromCdbHexOutput(sbValue);
  except:
    raise AssertionError(
      "Cannot parse value %s for %s:\r\n%s" % (
        repr(sbValue),
        sbRegister,
        "\r\n".join(fsCP437FromBytesString(sbLine) for sbLine in asbCommandOutput)
      )
    );
