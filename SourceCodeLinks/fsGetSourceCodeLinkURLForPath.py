from cBugIdTests import aoSourceCodeLinks as aoSourceCodeLinks_cBugIdTests;
from Chrome import aoSourceCodeLinks as aoSourceCodeLinks_Chrome;
from Firefox import aoSourceCodeLinks as aoSourceCodeLinks_Firefox;

aoSourceCodeLinks = (
  aoSourceCodeLinks_cBugIdTests
  + aoSourceCodeLinks_Chrome
  + aoSourceCodeLinks_Firefox
);

def fsGetSourceCodeLinkURLForPath(sPath, uLineNumber):
  for oSourceCodeLink in aoSourceCodeLinks:
    sLinkURL = oSourceCodeLink.fsGetURL(sPath, uLineNumber);
    if sLinkURL:
      return sLinkURL;
