import re;

cRegExp = type(re.compile(""));

NOT_PROVIDED = {};

class cBugTranslation(object):
  def __init__(oBugTranslation,
    sOriginalBugTypeId = NOT_PROVIDED, # Bug Type id as originally reported for this bug.
    asOriginalTopStackFrameSymbols = NOT_PROVIDED, # The top frames on the stack as originally reported for this bug.
    aasOriginalTopStackFrameSymbols = NOT_PROVIDED, # Multiple variations of the above
    sTranslatedBugTypeId = NOT_PROVIDED, # The Bug Type id that should be given to this bug if it matches.
    sTranslatedBugDescription = NOT_PROVIDED, # The Bug Description that should be given to this bug if it matches.
    sTranslatedSecurityImpact = NOT_PROVIDED, # The Bug Security impact that should be given to this bug if it matches.
    aasAdditionalIrrelevantStackFrameSymbols = NOT_PROVIDED,
  ):
    oBugTranslation.sOriginalBugTypeId = sOriginalBugTypeId;
    assert sOriginalBugTypeId is NOT_PROVIDED or isinstance(sOriginalBugTypeId, str) or isinstance(sOriginalBugTypeId, cRegExp), \
        "sOriginalBugTypeId must be a str of a regular expression object, not %s:%s" % \
        (type(sOriginalBugTypeId).__name__, repr(sOriginalBugTypeId));
    if aasOriginalTopStackFrameSymbols is not NOT_PROVIDED:
      assert asOriginalTopStackFrameSymbols is NOT_PROVIDED, \
          "asOriginalTopStackFrameSymbols XOR aasOriginalTopStackFrameSymbols";
      assert type(aasOriginalTopStackFrameSymbols) == list, \
          "aasOriginalTopStackFrameSymbols should be a list, got %s:%s" % \
          (type(aasOriginalTopStackFrameSymbols).__name__, repr(aasOriginalTopStackFrameSymbols));
      for asOriginalTopStackFrameSymbols in aasOriginalTopStackFrameSymbols:
        assert type(asOriginalTopStackFrameSymbols) == list, \
            "aasOriginalTopStackFrameSymbols should be a list with lists, got list with %s:%s" % \
            (type(asOriginalTopStackFrameSymbols).__name__, repr(asOriginalTopStackFrameSymbols));
        for sOriginalTopStackFrameSymbol in asOriginalTopStackFrameSymbols:
          assert type(sOriginalTopStackFrameSymbol) in [str, cRegExp], \
              "aasOriginalTopStackFrameSymbols should be a list with lists with strs or regular expressions, got list with lists with %s:%s" % \
              (type(sOriginalTopStackFrameSymbol).__name__, repr(sOriginalTopStackFrameSymbol));
      aasOriginalTopStackFrameSymbols.sort(key=len, reverse=True);
      oBugTranslation.aasOriginalTopStackFrameSymbols = aasOriginalTopStackFrameSymbols;
    elif asOriginalTopStackFrameSymbols is not NOT_PROVIDED:
      for sOriginalTopStackFrameSymbol in asOriginalTopStackFrameSymbols:
        assert type(sOriginalTopStackFrameSymbol) == str, \
            "asOriginalTopStackFrameSymbols should be a list with strs, got list with %s:%s" % \
            (type(sOriginalTopStackFrameSymbol).__name__, repr(sOriginalTopStackFrameSymbol));
      oBugTranslation.aasOriginalTopStackFrameSymbols = [asOriginalTopStackFrameSymbols];
    else:
      oBugTranslation.aasOriginalTopStackFrameSymbols = NOT_PROVIDED;
    # These must be sorted by array length (long to short) for foTranslateBug to work: if there are two entries with
    # the same symbols at the start, but one is longer, that one should be matched first.
    if aasAdditionalIrrelevantStackFrameSymbols is NOT_PROVIDED:
      aasAdditionalIrrelevantStackFrameSymbols = [];
    else:
      for asAdditionalIrrelevantStackFrameSymbols in aasAdditionalIrrelevantStackFrameSymbols:
        assert type(asAdditionalIrrelevantStackFrameSymbols) == list, \
            "aasAdditionalIrrelevantStackFrameSymbols should be a list with lists, got list with %s:%s" % \
            (type(asAdditionalIrrelevantStackFrameSymbols).__name__, repr(asAdditionalIrrelevantStackFrameSymbols));
        for sAdditionalIrrelevantStackFrameSymbol in asAdditionalIrrelevantStackFrameSymbols:
          assert type(sAdditionalIrrelevantStackFrameSymbol) in [str, cRegExp], \
              "aasAdditionalIrrelevantStackFrameSymbols should be a list with lists with strs or regular expressions, got list with lists with %s:%s" % \
              (type(sAdditionalIrrelevantStackFrameSymbol).__name__, repr(sAdditionalIrrelevantStackFrameSymbol));
      aasAdditionalIrrelevantStackFrameSymbols.sort(key=len, reverse=True);
    oBugTranslation.aasAdditionalIrrelevantStackFrameSymbols = aasAdditionalIrrelevantStackFrameSymbols;
    oBugTranslation.sTranslatedBugTypeId = sTranslatedBugTypeId;
    oBugTranslation.sTranslatedBugDescription = sTranslatedBugDescription;
    oBugTranslation.sTranslatedSecurityImpact = sTranslatedSecurityImpact;

  def fbApplyToBugReport(oBugTranslation, oBugReport):
    bTranslated = False;
    # If this translation is specific to certain bug types, check if it should be applied:
    if oBugTranslation.sOriginalBugTypeId is not NOT_PROVIDED:
      if oBugReport.sBugTypeId is None:
#        print "@@@ -%s: None" % repr(oBugTranslation.sOriginalBugTypeId);
        return False;
      elif isinstance(oBugTranslation.sOriginalBugTypeId, str):
        if oBugReport.sBugTypeId != oBugTranslation.sOriginalBugTypeId:
#          print "@@@ -%s: %s" % (repr(oBugTranslation.sOriginalBugTypeId), oBugReport.sBugTypeId);
          return False;
#        print "@@@ +%s" % repr(oBugTranslation.sOriginalBugTypeId);
      else:
        if not oBugTranslation.sOriginalBugTypeId.match(oBugReport.sBugTypeId):
#          print "@@@ -%s: %s" % (repr(oBugTranslation.sOriginalBugTypeId.pattern), oBugReport.sBugTypeId);
          return False;
#        print "@@@ %s" % repr(oBugTranslation.sOriginalBugTypeId.pattern);
    # If this translation is specific to certain top stack frames, check if it should be applied:
    if oBugTranslation.aasOriginalTopStackFrameSymbols is not NOT_PROVIDED:
      for asOriginalTopStackFrameSymbols in oBugTranslation.aasOriginalTopStackFrameSymbols:
        if oBugReport.oStack.fbTopFramesMatchSymbols(asOriginalTopStackFrameSymbols, \
            sHideWithReason = "this frame was used to translate this bug"):
          # Yes, and the top stack frames are hidden, so we've already translated it:
#          print "@@@ top frames";
          bTranslated = True;
          break;
      else:
        return False;
    # If more top frames may be irrelevant, see if they are there and hide them:
    while 1:
      bAdditionalIrrelevantFramesWereHidden = False;
      for asAdditionalIrrelevantStackFrameSymbols in oBugTranslation.aasAdditionalIrrelevantStackFrameSymbols:
        # Note that these should be ordered from longest to shortest array ^^^
        # This is done in the cBugTranslation constructor.
        if oBugReport.oStack.fbTopFramesMatchSymbols(asAdditionalIrrelevantStackFrameSymbols, \
            sHideWithReason = "this frame is irrelevant to this bug"):
#          print "@@@ hidden frames";
          bAdditionalIrrelevantFramesWereHidden = True;
          bTranslated = True;
          break;
      if not bAdditionalIrrelevantFramesWereHidden:
        break;
      # Some frames were hidden, see if we can hide more.
    # If the bug type should be translated, do so:
    if oBugTranslation.sTranslatedBugTypeId is not NOT_PROVIDED:
      oBugReport.sBugTypeId = oBugTranslation.sTranslatedBugTypeId;
      bTranslated = True;
    # If the bug description should be translated, do so:
    if oBugTranslation.sTranslatedBugDescription is not NOT_PROVIDED:
      oBugReport.sBugDescription = oBugTranslation.sTranslatedBugDescription;
      bTranslated = True;
    # If the security impact should be translated, do so:
    if oBugTranslation.sTranslatedSecurityImpact is not NOT_PROVIDED:
      oBugReport.sSecurityImpact = oBugTranslation.sTranslatedSecurityImpact;
      bTranslated = True;
    return bTranslated;
