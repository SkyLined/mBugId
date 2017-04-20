from CFG import aoBugTranslations as aoBugTranslations_CFG;
from Chrome import aoBugTranslations as aoBugTranslations_Chrome;
from Corpol import aoBugTranslations as aoBugTranslations_Corpol;
from Cpp import aoBugTranslations as aoBugTranslations_Cpp;
from Edge import aoBugTranslations as aoBugTranslations_Edge;
from Firefox import aoBugTranslations as aoBugTranslations_Firefox;
from ntdll import aoBugTranslations as aoBugTranslations_ntdll;
from MSIE import aoBugTranslations as aoBugTranslations_MSIE;

aoBugTranslations = aoBugTranslations_CFG \
                   + aoBugTranslations_Chrome \
                   + aoBugTranslations_Corpol \
                   + aoBugTranslations_Cpp \
                   + aoBugTranslations_Edge \
                   + aoBugTranslations_Firefox \
                   + aoBugTranslations_ntdll \
                   + aoBugTranslations_MSIE;

def foTranslateBug(oBugReport):
  # If there is a bug to report, check for a translation:
  if oBugReport is not None:
    for oBugTranslation in aoBugTranslations:
      # See if we have a matching bug type:
      if oBugReport.sBugTypeId == oBugTranslation.sOriginalBugTypeId:
        # See if we have a matching stack top:
        uFrameIndex = 0;
        while uFrameIndex < len(oBugReport.oStack.aoFrames) and oBugReport.oStack.aoFrames[uFrameIndex].bIsHidden:
          uFrameIndex += 1;
        for sOriginalStackTopFrameAddress in oBugTranslation.asOriginalStackTopFrameAddresses:
          if uFrameIndex >= len(oBugReport.oStack.aoFrames):
            break; # There are not enough stack frames to match this translation
          oTopFrame = oBugReport.oStack.aoFrames[uFrameIndex];
          uFrameIndex += 1;
          if sOriginalStackTopFrameAddress == None:
            # This frame should not have a symbol, if it does have a symbol, it cannot match.
            if oTopFrame.sSimplifiedAddress:
              break;
          else:
            # This frame should have a symbol, if it does not have a symbol, it cannot match.
            if not oTopFrame.sSimplifiedAddress:
              break;
            if sOriginalStackTopFrameAddress[:2] != "*!":
              if oTopFrame.sSimplifiedAddress.lower() != sOriginalStackTopFrameAddress.lower():
                # These frames don't match: stop checking frames
                break;
            else:
              # "*!" means match only the function and not the module.
              tsSimplifiedAddress = oTopFrame.sSimplifiedAddress.split("!", 1);
              # Compare the function names:
              if len(tsSimplifiedAddress) != 2 or tsSimplifiedAddress[1].lower() != sOriginalStackTopFrameAddress[2:].lower():
                # These frames don't match: stop checking frames
                break;
        else:
          # All frames matched: translate bug:
          if oBugTranslation.sTranslatedBugTypeId is None:
            # This is not a bug and should be ignored; the application can continue to run:
            return None;
          else:
            # Apply the translation:
            oBugReport.sBugTypeId = oBugTranslation.sTranslatedBugTypeId;
            oBugReport.sBugDescription = oBugTranslation.sTranslatedBugDescription;
            oBugReport.sSecurityImpact = oBugTranslation.sTranslatedSecurityImpact;
            # And hide all the matched frames as they are irrelevant
            for oFrame in oBugReport.oStack.aoFrames[:uFrameIndex]:
              oFrame.bIsHidden = True;
            # Give it another go in case this new bug is also translaterd.
            return foTranslateBug(oBugReport);
  # This bug (if any) cannot be translated and should be returned as-is.
  return oBugReport;
