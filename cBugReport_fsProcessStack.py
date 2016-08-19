from dxBugIdConfig import dxBugIdConfig;
import hashlib;

def cBugReport_fsProcessStack(oBugReport, oCdbWrapper):
  # Get a HTML representation of the stack, find the topmost relevatn stack frame and get stack id.
  uFramesHashed = 0;
  if oCdbWrapper.bGetDetailsHTML:
    asHTML = [];
  asStackFrameIds = [];
  oTopmostRelevantFrame = None;
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
      if oTopmostRelevantFrame is None:
        oTopmostRelevantFrame = oStackFrame;
      if oCdbWrapper.bGetDetailsHTML:
        asAddressClasses = [oStackFrame.oFunction and "StackFrameAddress" or "StackFrameNoSymbol"];
        if uFramesHashed < oBugReport.oStack.uHashFramesCount:
          asAddressClasses.append("Important");
      # Hash frame address for id and output frame to html
      if uFramesHashed < oBugReport.oStack.uHashFramesCount:
        asStackFrameIds.append(oStackFrame.sId or "?");
        # frame adds useful information to the id: add hash and output bold
        uFramesHashed += 1;
        if oCdbWrapper.bGetDetailsHTML:
          sOptionalHashHTML = " <span class=\"StackFrameHash\">(%s in id)</span>" % oCdbWrapper.fsHTMLEncode(oStackFrame.sId or "?");
    if oCdbWrapper.bGetDetailsHTML:
      sAddressHTML = "<span class=\"%s\">%s</span>" % (" ".join(asAddressClasses), oCdbWrapper.fsHTMLEncode(oStackFrame.sAddress));
      asHTML.append(sAddressHTML + sOptionalHashHTML + sOptionalSourceHTML);
  if len(asStackFrameIds) > dxBugIdConfig["uStackHashFramesCount"]:
    # For certain bugs, such as recursive function calls, ids may have been generated for more functions than the value
    # in uStackHashFramesCount. In this case, the last ids are hashes into one id to reduce the number of hashes:
    oHasher = hashlib.md5();
    while len(asStackFrameIds) >= dxBugIdConfig["uStackHashFramesCount"]:
      oHasher.update(asStackFrameIds.pop());
    asStackFrameIds.append(oHasher.hexdigest()[:dxBugIdConfig["uMaxStackFrameHashChars"]]);
  oBugReport.sStackId = ".".join([s for s in asStackFrameIds]);
  # Get the bug location.
  oBugReport.sBugLocation = "(unknown)";
  if oTopmostRelevantFrame:
    if oTopmostRelevantFrame.sSimplifiedAddress:
      oBugReport.sBugLocation = oTopmostRelevantFrame.sSimplifiedAddress;
    if oTopmostRelevantFrame.sSourceFilePath:
      oBugReport.sBugSourceLocation = "%s @ %d" % (oTopmostRelevantFrame.sSourceFilePath, oTopmostRelevantFrame.uSourceFileLineNumber);
  if (
      oBugReport.sProcessBinaryName and (
        not oTopmostRelevantFrame or
        not oTopmostRelevantFrame.oModule or
        oTopmostRelevantFrame.oModule.sBinaryName != oBugReport.sProcessBinaryName
     )
   ):
    # Exception happened in a module, not the process' binary: add process' binary name:
    oBugReport.sBugLocation = oBugReport.sProcessBinaryName + "!" + oBugReport.sBugLocation;
  oBugReport.oStack.oTopmostRelevantFrame = oTopmostRelevantFrame;
  if not oCdbWrapper.bGetDetailsHTML:
    return None;
  # Construct stack HTML
  return "<ol>%s</ol>%s" % (
    "".join(["<li>%s</li>" % s for s in asHTML]),
    oBugReport.oStack.bPartialStack and "There were more stack frames, but these were considered irrelevant and " \
        "subsequently ignored." or ""
  );
