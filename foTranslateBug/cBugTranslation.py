class cBugTranslation(object):
  def __init__(oBugTranslation,
    sOriginalBugTypeId,
    asOriginalStackTopFrameAddresses,
    sTranslatedBugTypeId,
    sTranslatedBugDescription,
    sTranslatedSecurityImpact,
  ):
    oBugTranslation.sOriginalBugTypeId = sOriginalBugTypeId;
    oBugTranslation.asOriginalStackTopFrameAddresses = asOriginalStackTopFrameAddresses;
    oBugTranslation.sTranslatedBugTypeId = sTranslatedBugTypeId;
    oBugTranslation.sTranslatedBugDescription = sTranslatedBugDescription;
    oBugTranslation.sTranslatedSecurityImpact = sTranslatedSecurityImpact;
