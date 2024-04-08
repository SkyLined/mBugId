import re;

from mNotProvided import (
  fAssertType,
  fbIsProvided,
  zNotProvided,
);

# local imports are at the end of this file to avoid import loops.

def fsRegExpToString(rRegExp):
  return "/%s/%s" % (
    fsCP437FromBytesString(rRegExp.pattern) if isinstance(rRegExp.pattern, bytes) else rRegExp.pattern,
    "".join([
      "a" if rRegExp.flags & re.A else "",
      "i" if rRegExp.flags & re.I else "",
      "l" if rRegExp.flags & re.L else "",
      "m" if rRegExp.flags & re.M else "",
      "s" if rRegExp.flags & re.S else "",
      "x" if rRegExp.flags & re.X else "",
    ])
  );

class cBugTranslation(object):
  def __init__(oSelf,
    srzOriginalBugTypeId =  zNotProvided, # RegExp matching any Bug Type id as originally reported for this bug.
    azs0rbAppliesOnlyToTopStackFrame = zNotProvided, # Multiple variations of the above
    s0zTranslatedBugTypeId = zNotProvided, # The Bug Type id that should be given to this bug if it matches.
    s0zTranslatedBugDescription = zNotProvided, # The Bug Description that should be given to this bug if it matches.
    s0zTranslatedSecurityImpact = zNotProvided, # The Bug Security impact that should be given to this bug if it matches.
    azs0rbAdditionalIrrelevantStackFrameSymbols = [],
    f0Callback = None,
    bDebug = False,
  ):
    if fbIsProvided(srzOriginalBugTypeId):
      fAssertType("srzOriginalBugTypeId", srzOriginalBugTypeId, str);
      oSelf.r0OriginalBugTypeId = re.compile("^(%s)$" % srzOriginalBugTypeId);
    else:
      oSelf.r0OriginalBugTypeId = None;
    
    if fbIsProvided(azs0rbAppliesOnlyToTopStackFrame):
      fAssertType("azs0rbAppliesOnlyToTopStackFrame", azs0rbAppliesOnlyToTopStackFrame, [bytes, None]);
      oSelf.bAppliesToNoneTopStackFrame = None in azs0rbAppliesOnlyToTopStackFrame;
      asrbAppliesOnlyToTopStackFrame = [
        s0rbAppliesOnlyToTopStackFrame
        for s0rbAppliesOnlyToTopStackFrame in azs0rbAppliesOnlyToTopStackFrame
        if s0rbAppliesOnlyToTopStackFrame is not None
      ];
      oSelf.rb0AppliesOnlyToTopStackFrame = re.compile(b"^(?:%s)$" % b"|".join([
        b"(?:%s)" % srbAppliesOnlyToTopStackFrame
        for srbAppliesOnlyToTopStackFrame in asrbAppliesOnlyToTopStackFrame
      ])) if len(asrbAppliesOnlyToTopStackFrame) > 0 else None;
    else:
      oSelf.bAppliesToNoneTopStackFrame = None;
      oSelf.rb0AppliesOnlyToTopStackFrame = None;
    
    if fbIsProvided(azs0rbAdditionalIrrelevantStackFrameSymbols):
      fAssertType("azs0rbAdditionalIrrelevantStackFrameSymbols", azs0rbAdditionalIrrelevantStackFrameSymbols, [bytes, None]);
      # These must be sorted by array length (long to short) for foTranslateBug to work: if there are two entries with
      # the same symbols at the start, but one is longer, that one should be matched first.
      oSelf.bAdditionalIrrelevantNoneTopStackFrames = None in azs0rbAdditionalIrrelevantStackFrameSymbols;
      asrbAdditionalIrrelevantStackFrameSymbols = [
        s0rbAdditionalIrrelevantStackFrameSymbols
        for s0rbAdditionalIrrelevantStackFrameSymbols in azs0rbAdditionalIrrelevantStackFrameSymbols
        if s0rbAdditionalIrrelevantStackFrameSymbols is not None
      ];
      oSelf.rb0AdditionalIrrelevantStackFrameSymbols = re.compile(b"^(?:%s)$" % b"|".join([
        b"(?:%s)" % srbAdditionalIrrelevantStackFrameSymbols
        for srbAdditionalIrrelevantStackFrameSymbols in asrbAdditionalIrrelevantStackFrameSymbols
      ])) if len(asrbAdditionalIrrelevantStackFrameSymbols) > 0 else None;
    else:
      oSelf.bAdditionalIrrelevantNoneTopStackFrames = False;
      oSelf.rb0AdditionalIrrelevantStackFrameSymbols = None;
    
    if fbIsProvided(s0zTranslatedBugTypeId): fAssertType("s0zTranslatedBugTypeId", s0zTranslatedBugTypeId, str, None);
    oSelf.s0zTranslatedBugTypeId = s0zTranslatedBugTypeId;
    
    if fbIsProvided(s0zTranslatedBugDescription): fAssertType("s0zTranslatedBugDescription", s0zTranslatedBugDescription, str, None);
    oSelf.s0zTranslatedBugDescription = s0zTranslatedBugDescription;
    
    if fbIsProvided(s0zTranslatedSecurityImpact): fAssertType("s0zTranslatedSecurityImpact", s0zTranslatedSecurityImpact, str, None);
    oSelf.s0zTranslatedSecurityImpact = s0zTranslatedSecurityImpact;
    
    oSelf.f0Callback = f0Callback;
    oSelf.bDebug = bDebug;
  
  def fbApplyToBugReport(oSelf, oCdbWrapper, oBugReport):
    # If this translation is specific to certain bug types, check if it should be applied:
    if (
      oSelf.r0OriginalBugTypeId and
      not oSelf.r0OriginalBugTypeId.match(oBugReport.s0BugTypeId)
    ):
      if oSelf.bDebug:
        oCdbWrapper.fbFireCallbacks("Log message", "Bug type id (%s) does not match %s" % (
          oBugReport.s0BugTypeId,
          fsRegExpToString(oSelf.r0OriginalBugTypeId),
        ));
      return False;
    bTranslated = False;
    # If this translation is specific to certain top stack frames, check if it should be applied:
    if oSelf.bAppliesToNoneTopStackFrame or oSelf.rb0AppliesOnlyToTopStackFrame:
      if oSelf.bDebug:
        sMatch = " or ".join([s for s in [
          fsRegExpToString(oSelf.rb0AppliesOnlyToTopStackFrame) if oSelf.rb0AppliesOnlyToTopStackFrame else None,
          "None" if oSelf.bAppliesToNoneTopStackFrame else None,
        ] if s]);
      if not oBugReport.o0Stack:
        if oSelf.bDebug:
          oCdbWrapper.fbFireCallbacks("Log message", "Bug has no stack, so does not match %s" % sMatch);
        return False;
      if oSelf.bDebug:
        uTopVisibleFrameIndex = 0;
        for oFrame in oBugReport.o0Stack.aoFrames:
          if oFrame.bHidden:
            uTopVisibleFrameIndex += 1;
          else:
            break;
        else:
          oCdbWrapper.fbFireCallbacks("Log message", "Bug stack is completely hidden, so does not match %s" % sMatch);
          return False;
      if not oBugReport.o0Stack.fbHideTopFramesIfTheyMatchSymbols(
        oSelf.rb0AppliesOnlyToTopStackFrame,
        "this frame was used to identify the type of bug",
        bAlsoHideNoneFrames = oSelf.bAppliesToNoneTopStackFrame,
      ):
        if oSelf.bDebug and uTopVisibleFrameIndex < len(oBugReport.o0Stack.aoFrames):
          oCdbWrapper.fbFireCallbacks("Log message", "Bug top visible stack frame (%s) does not match %s" % (
            oBugReport.o0Stack.aoFrames[uTopVisibleFrameIndex].sb0SimplifiedAddress,
            sMatch,
          ));
        return False;
      if oSelf.bDebug:
        for oFrame in oBugReport.o0Stack.aoFrames[uTopVisibleFrameIndex:]:
          if oFrame.bHidden:
            oCdbWrapper.fbFireCallbacks("Log message", "Bug top stack frame (%s) matches %s" % (
              oFrame.sb0SimplifiedAddress,
              sMatch,
            ));
      bTranslated = True;
    # If more top frames may be irrelevant, see if they are there and hide them:
    if (oSelf.bAdditionalIrrelevantNoneTopStackFrames or oSelf.rb0AdditionalIrrelevantStackFrameSymbols) and oBugReport.o0Stack:
      if oSelf.bDebug:
        sMatch = " or ".join([s for s in [
          fsRegExpToString(oSelf.rb0AdditionalIrrelevantStackFrameSymbols) if oSelf.rb0AdditionalIrrelevantStackFrameSymbols else None,
          "None" if oSelf.bAdditionalIrrelevantNoneTopStackFrames else None,
        ] if s]);
        uTopVisibleFrameIndex = 0;
        for oFrame in oBugReport.o0Stack.aoFrames:
          if oFrame.bHidden:
            uTopVisibleFrameIndex += 1;
          else:
            break;
        else:
          oCdbWrapper.fbFireCallbacks("Log message", "Bug stack is completely hidden, so can't hide frames matching %s" % sMatch);
      if not oBugReport.o0Stack.fbHideTopFramesIfTheyMatchSymbols(
        oSelf.rb0AdditionalIrrelevantStackFrameSymbols,
        "this frame is assumed to be irrelevant to this bug",
        bAlsoHideNoneFrames = oSelf.bAdditionalIrrelevantNoneTopStackFrames,
      ):
        if oSelf.bDebug and uTopVisibleFrameIndex < len(oBugReport.o0Stack.aoFrames):
          oCdbWrapper.fbFireCallbacks("Log message", "Bug top visible stack frame (%s) not hidden because it does not match %s" % (
            oBugReport.o0Stack.aoFrames[uTopVisibleFrameIndex].sb0SimplifiedAddress,
            sMatch,
          ));
        return False;
      else:
        if oSelf.bDebug:
          for oFrame in oBugReport.o0Stack.aoFrames[uTopVisibleFrameIndex:]:
            if oFrame.bHidden:
              oCdbWrapper.fbFireCallbacks("Log message", "Bug top stack frame (%s) hidden because it matches %s" % (
                oFrame.sb0SimplifiedAddress,
                sMatch,
              ));
        bTranslated = True;
    # If the bug type should be translated, do so:
    if fbIsProvided(oSelf.s0zTranslatedBugTypeId):
      if oSelf.bDebug:
        oCdbWrapper.fbFireCallbacks("Log message", "Bug type translated from %s to %s" % (
          oBugReport.s0BugTypeId,
          oSelf.s0zTranslatedBugTypeId,
        ));
      oBugReport.s0BugTypeId = oSelf.s0zTranslatedBugTypeId;
      bTranslated = True;
    # If the bug description should be translated, do so:
    if fbIsProvided(oSelf.s0zTranslatedBugDescription):
      if oSelf.bDebug:
        oCdbWrapper.fbFireCallbacks("Log message", "Bug description translated from %s to %s" % (
          oBugReport.s0BugDescription,
          oSelf.s0zTranslatedBugDescription,
        ));
      oBugReport.s0BugDescription = oSelf.s0zTranslatedBugDescription;
      bTranslated = True;
    # If the security impact should be translated, do so:
    if fbIsProvided(oSelf.s0zTranslatedSecurityImpact):
      if oSelf.bDebug:
        oCdbWrapper.fbFireCallbacks("Log message", "Bug security impact translated from %s to %s" % (
          oBugReport.s0SecurityImpact,
          oSelf.s0zTranslatedSecurityImpact,
        ));
      oBugReport.s0SecurityImpact = oSelf.s0zTranslatedSecurityImpact;
      bTranslated = True;
    if oSelf.f0Callback:
      if oSelf.bDebug:
        oCdbWrapper.fbFireCallbacks("Log message", "Running bug call back %s @ %s line %s" % (
          oSelf.f0Callback.__code__.co_name,
          oSelf.f0Callback.__code__.co_filename,
          oSelf.f0Callback.__code__.co_firstlineno,
        ));
      oSelf.f0Callback(oCdbWrapper, oBugReport);
    return bTranslated;

from ..mCP437 import fsCP437FromBytesString;
