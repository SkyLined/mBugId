from fsGetNumberDescription import fsGetNumberDescription;

def fsGetOffsetDescription(iOffset):
  if iOffset == 0:
    return "";
  sSign = iOffset < 0 and "-" or "+";
  return "%s%s" % (sSign, fsGetNumberDescription(abs(iOffset), sSign));

