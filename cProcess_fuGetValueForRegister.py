def cProcess_fuGetValueForRegister(oProcess, sRegister, sComment):
  # This is a register or pseudo-register: it's much faster to get these using the "r" command than printing them
  # as is done for other values:
  asCommandOutput = oProcess.fasExecuteCdbCommand(
    sCommand = "r @%s;" % sRegister,
    sComment = sComment,
  );
  assert len(asCommandOutput) == 1, \
      "Expected exactly one line in \"r\" command output:\r\n%s" % "\r\n".join(asCommandOutput);
  asRegisterAndValueResult = asCommandOutput[0].split("=", 1);
  assert len(asRegisterAndValueResult) == 2, \
      "Missing \"=\" in result:\r\n%s" % "\r\n".join(asCommandOutput);
  sRegisterResult, sValue = asRegisterAndValueResult;
  assert sRegisterResult.lower() == sRegister.lower(), \
      "Expected result to start with %s, not %s\r\n%s" % \
      (repr(sRegister.lower() + "="), repr(sRegisterResult + "="), "\r\n".join(asCommandOutput));
  try:
    return long(sValue, 16);
  except:
    raise AssertionError("Cannot parse value %s for %s:\r\n%s" % (repr(sValue), sRegister, "\r\n".join(asCommandOutput)));
