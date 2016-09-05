import hashlib;
from dxBugIdConfig import dxBugIdConfig;

def cBugReport_fxProcessStack(oBugReport, oCdbWrapper):
  # Get a HTML representation of the stack, find the topmost relevatn stack frame and get stack id.
  uFramesHashed = 0;
  if oCdbWrapper.bGetDetailsHTML:
    asHTML = [];
    asNotesHTML = [];
  aoRelevantStackFrames = [];
  for oStackFrame in oBugReport.oStack.aoFrames:
    if oCdbWrapper.bGetDetailsHTML:
      sOptionalHashHTML = "";
      sOptionalSourceHTML = "";
      if oStackFrame.sSourceFilePath:
        sSourceFilePathAndLineNumber = "%s @ %d" % (oStackFrame.sSourceFilePath, oStackFrame.uSourceFileLineNumber);
        sOptionalSourceHTML = " <span class=\"StackSource\">[%s]</span>" % oCdbWrapper.fsHTMLEncode(sSourceFilePathAndLineNumber);
    if oStackFrame.bIsHidden:
      # This frame is hidden (because it is irrelevant to the crash)
      if oCdbWrapper.bGetDetailsHTML:
        asAddressClasses = ["StackFrameIgnored"];
    else:
      if oCdbWrapper.bGetDetailsHTML:
        asAddressClasses = [oStackFrame.oFunction and "StackFrameAddress" or "StackFrameNoSymbol"];
        if uFramesHashed < oBugReport.oStack.uHashFramesCount:
          asAddressClasses.append("Important");
      # Hash frame address for id and output frame to html
      if uFramesHashed < oBugReport.oStack.uHashFramesCount:
        aoRelevantStackFrames.append(oStackFrame);
        # frame adds useful information to the id: add hash and output bold
        uFramesHashed += 1;
        if oCdbWrapper.bGetDetailsHTML:
          sOptionalHashHTML = " <span class=\"StackFrameHash\">(id: %s)</span>" % oCdbWrapper.fsHTMLEncode(oStackFrame.sId or "?");
    if oCdbWrapper.bGetDetailsHTML:
      sAddressHTML = "<span class=\"%s\">%s</span>" % (" ".join(asAddressClasses), oCdbWrapper.fsHTMLEncode(oStackFrame.sAddress));
      asHTML.append(sAddressHTML + sOptionalHashHTML + sOptionalSourceHTML);
  asStackFrameIds = [oStackFrame.sId or "_" for oStackFrame in aoRelevantStackFrames];
  if len(asStackFrameIds) > dxBugIdConfig["uStackHashFramesCount"]:
    # For certain bugs, such as recursive function calls, ids may have been generated for more functions than the value
    # in uStackHashFramesCount. In this case, the last ids are hashes into one id to reduce the number of hashes:
    oHasher = hashlib.md5();
    asCombinedIds = [];
    while len(asStackFrameIds) >= dxBugIdConfig["uStackHashFramesCount"]:
      sId = asStackFrameIds.pop();
      asCombinedIds.append(sId);
      oHasher.update(sId);
    sCombinedId = oHasher.hexdigest()[:dxBugIdConfig["uMaxStackFrameHashChars"]];
    asStackFrameIds.append(sCombinedId);
    asNotesHTML += ["The stack frames with ids %s and %s where combined into one id %s." % \
        (", ".join(asCombinedIds[:-1]), asCombinedIds[-1], sCombinedId)];
  oBugReport.sStackId = ".".join([s for s in asStackFrameIds]);
  # Get the bug location.
  oBugReport.sBugLocation = "(unknown)";
  if aoRelevantStackFrames:
    if aoRelevantStackFrames[0].sSimplifiedAddress:
      oBugReport.sBugLocation = aoRelevantStackFrames[0].sSimplifiedAddress;
    if aoRelevantStackFrames[0].sSourceFilePath:
      oBugReport.sBugSourceLocation = "%s @ %d" % \
          (aoRelevantStackFrames[0].sSourceFilePath, aoRelevantStackFrames[0].uSourceFileLineNumber);
  if (
      oBugReport.sProcessBinaryName and (
        not aoRelevantStackFrames[0] or
        not aoRelevantStackFrames[0].oModule or
        aoRelevantStackFrames[0].oModule.sBinaryName != oBugReport.sProcessBinaryName
     )
   ):
    # Exception happened in a module, not the process' binary: add process' binary name:
    oBugReport.sBugLocation = oBugReport.sProcessBinaryName + "!" + oBugReport.sBugLocation;
  if oCdbWrapper.bGetDetailsHTML:
    if oBugReport.oStack.bPartialStack:
      asNotesHTML += ["There were more stack frames than shown above, but these were not considered relevant."];
    sHTML = "".join([
      asHTML      and "<ol>%s</ol>" % "".join(["<li>%s</li>" % s for s in asHTML]) or "",
      asNotesHTML and "<ul>%s</ul>" % "".join(["<li>%s</li>" % s for s in asNotesHTML]) or "",
    ]);
  else:
    sHTML = None;
  return aoRelevantStackFrames, sHTML;