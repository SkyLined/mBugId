import re;

class cSourceCodeLink(object):
  def __init__(oSourceCodeLink, srPathHeader, sFileOnlyURLTemplate, sFileAndLineNumberURLTemplate = None):
    oSourceCodeLink.rPathHeader = re.compile(srPathHeader, re.I);
    oSourceCodeLink.sFileOnlyURLTemplate = sFileOnlyURLTemplate;
    oSourceCodeLink.sFileAndLineNumberURLTemplate = sFileAndLineNumberURLTemplate or sFileOnlyURLTemplate;
  
  def fsGetURL(oSourceCodeLink, sPath, uLineNumber):
    oMatch = oSourceCodeLink.rPathHeader.match(sPath);
    if not oMatch:
      return;
    return (
      uLineNumber is None
          and oSourceCodeLink.sFileOnlyURLTemplate
          or oSourceCodeLink.sFileAndLineNumberURLTemplate
    ) % {
      "path": sPath[oMatch.end():].replace("\\", "/"),
      "line_number": uLineNumber,
    };
