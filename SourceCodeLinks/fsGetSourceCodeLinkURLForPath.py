from cBugIdTests import aoSourceCodeLinks as aoSourceCodeLinks_cBugIdTests;
from Chrome import aoSourceCodeLinks as aoSourceCodeLinks_Chrome;

aoSourceCodeLinks = (
  aoSourceCodeLinks_cBugIdTests
  + aoSourceCodeLinks_Chrome
);

def fsGetSourceCodeLinkURLForPath(sPath, uLineNumber):
  for oSourceCodeLink in aoSourceCodeLinks:
    sLinkURL = oSourceCodeLink.fsGetURL(sPath, uLineNumber);
    if sLinkURL:
      return sLinkURL;
