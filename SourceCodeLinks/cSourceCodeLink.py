import re;

class cSourceCodeLink(object):
  def __init__(oSourceCodeLink, srPathHeader, sURLTemplate):
    oSourceCodeLink.rPathHeader = re.compile(srPathHeader, re.I);
    oSourceCodeLink.sURLTemplate = sURLTemplate;
  
  def fsGetURL(oSourceCodeLink, sPath, uLineNumber):
    oMatch = oSourceCodeLink.rPathHeader.match(sPath);
    if not oMatch:
      return;
    return oSourceCodeLink.sURLTemplate % {
      "path": sPath[oMatch.end():].replace("\\", "/"),
      "line_number": uLineNumber,
    };
