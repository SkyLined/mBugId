def ftsReportProductHeaderAndFooterHTML(oProductDetails):
  sProductHeaderHTML = '<a href="%(sProductURL)s">%(sProductName)s</a> version %(sProductVersion)s by %(sProductAuthor)s.' % {
    "sProductName": oProductDetails.sProductName,
    "sProductVersion": oProductDetails.oProductVersion,
    "sProductAuthor": oProductDetails.sProductAuthor,
    "sProductURL": str(oProductDetails.sb0ProductURL, "ascii", "strict"),
  };
  sProductFooter = 'This report was generated using <a href="%(sProductURL)s">%(sProductName)s version %(sProductVersion)s</a> by %(sProductAuthor)s</a>.<br/>'% {
    "sProductName": oProductDetails.sProductName,
    "sProductVersion": oProductDetails.oProductVersion,
    "sProductAuthor": oProductDetails.sProductAuthor,
    "sProductURL": str(oProductDetails.sb0ProductURL, "ascii", "strict"),
  };
  return (sProductHeaderHTML, sProductFooter);
