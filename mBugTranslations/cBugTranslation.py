import re;

from mNotProvided import *;

class cBugTranslation(object):
  def __init__(oSelf,
    srzOriginalBugTypeId =  zNotProvided, # RegExp matching any Bug Type id as originally reported for this bug.
    azsrbAppliesOnlyToTopStackFrame = zNotProvided, # Multiple variations of the above
    s0zTranslatedBugTypeId = zNotProvided, # The Bug Type id that should be given to this bug if it matches.
    s0zTranslatedBugDescription = zNotProvided, # The Bug Description that should be given to this bug if it matches.
    s0zTranslatedSecurityImpact = zNotProvided, # The Bug Security impact that should be given to this bug if it matches.
    asrbAdditionalIrrelevantStackFrameSymbols = [],
    f0Callback = None,
  ):
    if fbIsProvided(srzOriginalBugTypeId):
      fAssertType("srzOriginalBugTypeId", srzOriginalBugTypeId, str);
      oSelf.r0OriginalBugTypeId = re.compile("^(%s)$" % srzOriginalBugTypeId);
    else:
      oSelf.r0OriginalBugTypeId = None;
    
    if fbIsProvided(azsrbAppliesOnlyToTopStackFrame):
      fAssertType("azsrbAppliesOnlyToTopStackFrame", azsrbAppliesOnlyToTopStackFrame, [bytes]);
      oSelf.rb0AppliesOnlyToTopStackFrame = re.compile(b"^(?:%s)$" % b"|".join([
        b"(?:%s)" % srbAppliesOnlyToTopStackFrame
        for srbAppliesOnlyToTopStackFrame in azsrbAppliesOnlyToTopStackFrame
      ]));
    else:
      oSelf.rb0AppliesOnlyToTopStackFrame = None;
    
    fAssertType("asrbAdditionalIrrelevantStackFrameSymbols", asrbAdditionalIrrelevantStackFrameSymbols, [bytes]);
    # These must be sorted by array length (long to short) for foTranslateBug to work: if there are two entries with
    # the same symbols at the start, but one is longer, that one should be matched first.
    oSelf.rb0AdditionalIrrelevantStackFrameSymbols = re.compile(b"^(?:%s)$" % b"|".join([
      b"(?:%s)" % srbAdditionalIrrelevantStackFrameSymbols
      for srbAdditionalIrrelevantStackFrameSymbols in asrbAdditionalIrrelevantStackFrameSymbols
    ])) if asrbAdditionalIrrelevantStackFrameSymbols else None;
    
    if fbIsProvided(s0zTranslatedBugTypeId): fAssertType("s0zTranslatedBugTypeId", s0zTranslatedBugTypeId, str, None);
    oSelf.s0zTranslatedBugTypeId = s0zTranslatedBugTypeId;
    
    if fbIsProvided(s0zTranslatedBugDescription): fAssertType("s0zTranslatedBugDescription", s0zTranslatedBugDescription, str, None);
    oSelf.s0zTranslatedBugDescription = s0zTranslatedBugDescription;
    
    if fbIsProvided(s0zTranslatedSecurityImpact): fAssertType("s0zTranslatedSecurityImpact", s0zTranslatedSecurityImpact, str, None);
    oSelf.s0zTranslatedSecurityImpact = s0zTranslatedSecurityImpact;
    
    oSelf.f0Callback = f0Callback;
  
  def fbApplyToBugReport(oSelf, oCdbWrapper, oBugReport):
    # If this translation is specific to certain bug types, check if it should be applied:
    if (
      oSelf.r0OriginalBugTypeId and
      not oSelf.r0OriginalBugTypeId.match(oBugReport.s0BugTypeId)
    ):
      return False;
    bTranslated = False;
    # If this translation is specific to certain top stack frames, check if it should be applied:
    if oSelf.rb0AppliesOnlyToTopStackFrame:
      if not oBugReport.o0Stack or not oBugReport.o0Stack.fbHideTopFramesIfTheyMatchSymbols(
        oSelf.rb0AppliesOnlyToTopStackFrame,
        "this frame was used to identify the type of bug",
      ):
        return False;
      bTranslated = True;
    # If more top frames may be irrelevant, see if they are there and hide them:
    if oSelf.rb0AdditionalIrrelevantStackFrameSymbols and oBugReport.o0Stack and oBugReport.o0Stack.fbHideTopFramesIfTheyMatchSymbols(
      oSelf.rb0AdditionalIrrelevantStackFrameSymbols,
      "this frame is assumed to be irrelevant to this bug"
    ):
      bTranslated = True;
    # If the bug type should be translated, do so:
    if fbIsProvided(oSelf.s0zTranslatedBugTypeId):
      oBugReport.s0BugTypeId = oSelf.s0zTranslatedBugTypeId;
      bTranslated = True;
    # If the bug description should be translated, do so:
    if fbIsProvided(oSelf.s0zTranslatedBugDescription):
      oBugReport.s0BugDescription = oSelf.s0zTranslatedBugDescription;
      bTranslated = True;
    # If the security impact should be translated, do so:
    if fbIsProvided(oSelf.s0zTranslatedSecurityImpact):
      oBugReport.s0SecurityImpact = oSelf.s0zTranslatedSecurityImpact;
      bTranslated = True;
    if oSelf.f0Callback:
      oSelf.f0Callback(oCdbWrapper, oBugReport);
    return bTranslated;
