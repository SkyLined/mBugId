from .mCP437 import fsCP437FromBytesString;

def ftsReportProductHeaderAndFooterHTML(oProductDetails):
  sProductHeaderHTML = '<a href="%(sProductURL)s">%(sProductName)s</a> version %(sProductVersion)s by %(sProductAuthor)s.' % {
    "sProductName": oProductDetails.sProductName,
    "sProductVersion": oProductDetails.oProductVersion,
    "sProductAuthor": oProductDetails.sProductAuthor,
    "sProductURL": fsCP437FromBytesString(oProductDetails.sb0ProductURL),
  };
  sProductFooter = 'This report was generated using <a href="%(sProductURL)s">%(sProductName)s version %(sProductVersion)s</a> by %(sProductAuthor)s</a>.<br/>'% {
    "sProductName": oProductDetails.sProductName,
    "sProductVersion": oProductDetails.oProductVersion,
    "sProductAuthor": oProductDetails.sProductAuthor,
    "sProductURL": fsCP437FromBytesString(oProductDetails.sb0ProductURL),
  };
  return (sProductHeaderHTML, sProductFooter);
