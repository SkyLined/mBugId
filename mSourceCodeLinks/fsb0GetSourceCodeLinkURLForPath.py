from .cBugIdTests import aoSourceCodeLinks as aoSourceCodeLinks_cBugIdTests;
from .Chrome import aoSourceCodeLinks as aoSourceCodeLinks_Chrome;
from .Firefox import aoSourceCodeLinks as aoSourceCodeLinks_Firefox;

aoSourceCodeLinks = (
  aoSourceCodeLinks_cBugIdTests
  + aoSourceCodeLinks_Chrome
  + aoSourceCodeLinks_Firefox
);

def fsb0GetSourceCodeLinkURLForPath(sbPath, uLineNumber):
  for oSourceCodeLink in aoSourceCodeLinks:
    sb0LinkURL = oSourceCodeLink.fsbGetURL(sbPath, uLineNumber);
    if sb0LinkURL:
      return sb0LinkURL;
  return None;
