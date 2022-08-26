from .mCP437 import fsCP437FromBytesString;

def ftsReportProductHeaderAndFooterHTML(oProductDetails):
  sProductHeaderHTML = (
    "<span class=\"ProductInfo\">"
      "<a href=\"%(sProductURL)s\">%(sProductName)s version %(sProductVersion)s</a>"
      " by %(sProductAuthor)s."
    "</span>"
  ) % {
    "sProductName": oProductDetails.sProductName,
    "sProductVersion": oProductDetails.oProductVersion,
    "sProductAuthor": oProductDetails.sProductAuthor,
    "sProductURL": fsCP437FromBytesString(oProductDetails.sb0ProductURL),
  };
  sProductFooter = (
    "<span class=\"ProductInfo\">"
      "This report was generated using "
      "<a href=\"%(sProductURL)s\">%(sProductName)s version %(sProductVersion)s</a>"
      " by %(sProductAuthor)s.<br/>"
    "</span>"
  ) % {
    "sProductName": oProductDetails.sProductName,
    "sProductVersion": oProductDetails.oProductVersion,
    "sProductAuthor": oProductDetails.sProductAuthor,
    "sProductURL": fsCP437FromBytesString(oProductDetails.sb0ProductURL),
  };
  return (sProductHeaderHTML, sProductFooter);
