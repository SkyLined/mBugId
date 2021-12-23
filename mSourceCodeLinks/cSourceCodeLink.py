import re;

class cSourceCodeLink(object):
  def __init__(oSelf, srbPathHeader, sbFileOnlyURLTemplate, sbFileAndLineNumberURLTemplate = None):
    oSelf.rbPathHeader = re.compile(srbPathHeader, re.I);
    oSelf.sbFileOnlyURLTemplate = sbFileOnlyURLTemplate;
    oSelf.sbFileAndLineNumberURLTemplate = sbFileAndLineNumberURLTemplate or sbFileOnlyURLTemplate;
  
  def fsbGetURL(oSelf, sbPath, u0LineNumber):
    oMatch = oSelf.rbPathHeader.match(sbPath);
    if not oMatch:
      return;
    sbURLTemplate = oSelf.sbFileOnlyURLTemplate if u0LineNumber is None else oSelf.sbFileAndLineNumberURLTemplate;
    return sbURLTemplate % {
      b"path": sbPath[oMatch.end():].replace(b"\\", b"/"),
      b"line_number": None if u0LineNumber is None else b"%d" % u0LineNumber,
    };
