import re;
from .fsHTMLCP437 import fsHTMLCP437;

def fsHTMLEncodeLine(sString, uTabStop, bCP437):
  asResult = [];
  uLineIndex = 0;
  for sChar in sString:
    if uTabStop is not None and sChar == "\t":
      while 1:
        asResult.append("&nbsp;");
        uLineIndex += 1;
        if uLineIndex % uTabStop == 0: break;
    else:
      asResult.append(
        fsHTMLCP437(sChar) if bCP437 else 
        sChar if (0x20 <= ord(sChar) <= 0x7E) else
        "&#%d;" % ord(sChar)
      );
      uLineIndex += 1;
  return "".join(asResult);

def cCdbWrapper_fsHTMLEncode(oCdbWrapper, sxLine, uTabStop = None):
  if isinstance(sxLine, str):
    sLine = sxLine;
    bCP437 = False;
  else:
    sLine = str(sxLine, 'latin1');
    bCP437 = True;
  # Convert to HTML and add links to the first reference to source code. Adding links to all references would be rather
  # complex and since I've not encountered situations where this is needed, so I've kept it simple.
  for (srSourceFilePath, sURLTemplate) in oCdbWrapper.dsURLTemplate_by_srSourceFilePath.items():
    oMatch = re.search(srSourceFilePath, sLine);
    if oMatch:
      sBefore = sLine[:oMatch.start()];
      sPath = oMatch.group(0);
      sURL = (sURLTemplate % oMatch.groupdict()).replace("\\", "/");
      sAfter = sLine[oMatch.end():];
      return '%s<a target="_blank" href="%s">%s</a>%s' % (fsHTMLEncodeLine(sBefore, uTabStop, bCP437), sURL, \
          fsHTMLEncodeLine(sPath, uTabStop, bCP437), fsHTMLEncodeLine(sAfter, uTabStop, bCP437));
  return fsHTMLEncodeLine(sLine, uTabStop, bCP437);
