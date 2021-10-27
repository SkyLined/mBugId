class cEndOfCommandOutputMarkerMissingException(Exception):
  def __init__(oSelf, asbCommandOutput):
    oSelf.asbCommandOutput = asbCommandOutput;
  def __str__(oSelf):
    return "The 'End-of-Command-Output Marker' is missing from the command output:\r\n%s" % "\r\n".join(oSelf.asbCommandOutput);
