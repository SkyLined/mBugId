import re;
from fsHTMLCP437 import fsHTMLCP437;
def fsHTMLEncodeString(sString):
  return "".join([fsHTMLCP437(sChar) for sChar in sString]);

def cCdbWrapper_fsHTMLEncode(oCdbWrapper, sLine):
  # This will only apply a link to the first match, but improving it would be rather complex. Since I've not encountered
  # a situation where more than one links is needed, I've kept it simple.
  for (srSourceFilePath, sURLTemplate) in oCdbWrapper.dsURLTemplate_by_srSourceFilePath.items():
    oMatch = re.search(srSourceFilePath, sLine);
    if oMatch:
      sBefore = sLine[:oMatch.start()];
      sPath = oMatch.group(0);
      sURL = (sURLTemplate % oMatch.groupdict()).replace("\\", "/");
      sAfter = sLine[oMatch.end():];
      return "%s<a target=\"_blank\" href=\"%s\">%s</a>%s" % \
          (fsHTMLEncodeString(sBefore), sURL, fsHTMLEncodeString(sPath), fsHTMLEncodeString(sAfter));
  else:
    return fsHTMLEncodeString(sLine);

