import re;
from .fsHTMLCP437 import fsHTMLCP437;

def fsHTMLEncodeLine(sString, uTabStop = None):
  asResult = [];
  uLineIndex = 0;
  for sChar in sString:
    if uTabStop is not None and sChar == "\t":
      while 1:
        asResult.append("&nbsp;");
        uLineIndex += 1;
        if uLineIndex % uTabStop == 0: break;
    else:
      asResult.append(fsHTMLCP437(sChar));
      uLineIndex += 1;
  return "".join(asResult);

def cCdbWrapper_fsHTMLEncode(oCdbWrapper, sLine, uTabStop = None):
  # Convert to HTML and add links to the first reference to source code. Adding links to all references would be rather
  # complex and since I've not encountered situations where this is needed, so I've kept it simple.
  for (srSourceFilePath, sURLTemplate) in oCdbWrapper.dsURLTemplate_by_srSourceFilePath.items():
    oMatch = re.search(srSourceFilePath, sLine);
    if oMatch:
      sBefore = sLine[:oMatch.start()];
      sPath = oMatch.group(0);
      sURL = (sURLTemplate % oMatch.groupdict()).replace("\\", "/");
      sAfter = sLine[oMatch.end():];
      return '%s<a target="_blank" href="%s">%s</a>%s' % (fsHTMLEncodeLine(sBefore, uTabStop), sURL, \
          fsHTMLEncodeLine(sPath, uTabStop), fsHTMLEncodeLine(sAfter, uTabStop));
  return fsHTMLEncodeLine(sLine, uTabStop);
