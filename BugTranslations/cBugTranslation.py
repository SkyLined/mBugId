NOT_PROVIDED = {};


class cBugTranslation(object):
  def __init__(oBugTranslation,
    sOriginalBugTypeId, # Bug Type id as originally reported for this bug.
    asOriginalTopStackFrameSymbols = NOT_PROVIDED, # The top frames on the stack as originally reported for this bug.
    aasOriginalTopStackFrameSymbols = NOT_PROVIDED, # Multiple variations of the above
    sTranslatedBugTypeId = NOT_PROVIDED, # The Bug Type id that should be given to this bug if it matches.
    sTranslatedBugDescription = NOT_PROVIDED, # The Bug Description that should be given to this bug if it matches.
    sTranslatedSecurityImpact = NOT_PROVIDED, # The Bug Security impact that should be given to this bug if it matches.
    aasAdditionalIrrelevantStackFrameSymbols = NOT_PROVIDED,
  ):
    oBugTranslation.sOriginalBugTypeId = sOriginalBugTypeId;
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
          assert type(sOriginalTopStackFrameSymbol) == str, \
              "aasOriginalTopStackFrameSymbols should be a list with lists with strs, got list with lists with %s:%s" % \
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
      aasAdditionalIrrelevantStackFrameSymbols.sort(key=len, reverse=True);
    oBugTranslation.aasAdditionalIrrelevantStackFrameSymbols = aasAdditionalIrrelevantStackFrameSymbols;
    oBugTranslation.sTranslatedBugTypeId = sTranslatedBugTypeId;
    oBugTranslation.sTranslatedBugDescription = sTranslatedBugDescription;
    oBugTranslation.sTranslatedSecurityImpact = sTranslatedSecurityImpact;

  def fbApplyToBugReport(oBugTranslation, oBugReport):
    # See if we have a matching bug type:
    if oBugReport.sBugTypeId != oBugTranslation.sOriginalBugTypeId:
      return False;
    # See if we have matching top stack frames:
    if oBugTranslation.aasOriginalTopStackFrameSymbols is NOT_PROVIDED:
      bTranslated = False;
    else:
      for asOriginalTopStackFrameSymbols in oBugTranslation.aasOriginalTopStackFrameSymbols:
        if oBugReport.oStack.fbTopFramesMatchSymbols(asOriginalTopStackFrameSymbols, bHideIfMatched = True):
          break;
      else:
        return False;
      bTranslated = True;
    # It's a match: translate bug:
    if oBugTranslation.sTranslatedBugTypeId is not NOT_PROVIDED:
      oBugReport.sBugTypeId = oBugTranslation.sTranslatedBugTypeId;
      bTranslated = True;
    if oBugTranslation.sTranslatedBugDescription is not NOT_PROVIDED:
      oBugReport.sBugDescription = oBugTranslation.sTranslatedBugDescription;
      bTranslated = True;
    if oBugTranslation.sTranslatedSecurityImpact is not NOT_PROVIDED:
      oBugReport.sSecurityImpact = oBugTranslation.sTranslatedSecurityImpact;
      bTranslated = True;
    # Optionally hide some more irrelevant frames:
    for asAdditionalIrrelevantStackFrameSymbols in oBugTranslation.aasAdditionalIrrelevantStackFrameSymbols:
      # Note that these should be ordered from longest to shortest array ^^^
      # This is done in the cBugTranslation constructor.
      if oBugReport.oStack.fbTopFramesMatchSymbols(asAdditionalIrrelevantStackFrameSymbols, bHideIfMatched = True):
        bTranslated = True;
        break;
    return bTranslated;
