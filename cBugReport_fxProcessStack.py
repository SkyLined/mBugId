import hashlib;
from dxConfig import dxConfig;

def cBugReport_fxProcessStack(oBugReport, oCdbWrapper):
  # Get a HTML representation of the stack, find the topmost relevant stack frame and get stack id.
  if oCdbWrapper.bGenerateReportHTML:
    asHTML = [];
    asNotesHTML = [];
  asStackFrameIds = [];
  aoRelevantStackFrames = [];
  for oStackFrame in oBugReport.oStack.aoFrames:
    if oCdbWrapper.bGenerateReportHTML:
      sOptionalHashHTML = "";
      sOptionalSourceHTML = "";
      if oStackFrame.sSourceFilePath:
        sSourceFilePathAndLineNumber = "%s @ %d" % (oStackFrame.sSourceFilePath, oStackFrame.uSourceFileLineNumber);
        sOptionalSourceHTML = " <span class=\"StackSource\">[%s]</span>" % \
            oCdbWrapper.fsHTMLEncode(sSourceFilePathAndLineNumber);
    if oStackFrame.bIsHidden:
      # This frame is hidden (because it is irrelevant to the crash)
      if oCdbWrapper.bGenerateReportHTML:
        asAddressClasses = ["StackFrameIgnored"];
    else:
      if oCdbWrapper.bGenerateReportHTML:
        asAddressClasses = [oStackFrame.oFunction and "StackFrameAddress" or "StackFrameNoSymbol"];
        if len(asStackFrameIds) < oBugReport.oStack.uHashFramesCount and oStackFrame.sId:
          asAddressClasses.append("Important");
      # Hash frame address for id and output frame to html
      if len(asStackFrameIds) < oBugReport.oStack.uHashFramesCount:
        aoRelevantStackFrames.append(oStackFrame);
        if oStackFrame.sId:
          asStackFrameIds.append(oStackFrame.sId);
          if oCdbWrapper.bGenerateReportHTML:
            # frame adds useful information to the id: add hash and output bold
            sOptionalHashHTML = " <span class=\"StackFrameHash\">(id: %s)</span>" % \
                oCdbWrapper.fsHTMLEncode(oStackFrame.sId);
    if oCdbWrapper.bGenerateReportHTML:
      sAddressHTML = "<span class=\"%s\">%s</span>" % \
          (" ".join(asAddressClasses), oCdbWrapper.fsHTMLEncode(oStackFrame.sAddress));
      asHTML.append(sAddressHTML + sOptionalHashHTML + sOptionalSourceHTML);
  if len(asStackFrameIds) > dxConfig["uStackHashFramesCount"]:
    # For certain bugs, such as recursive function calls, ids may have been generated for more functions than the value
    # in uStackHashFramesCount. In this case, the last ids are hashes into one id to reduce the number of hashes:
    oHasher = hashlib.md5();
    asCombinedIds = [];
    while len(asStackFrameIds) >= dxConfig["uStackHashFramesCount"]:
      sId = asStackFrameIds.pop();
      asCombinedIds.append(sId);
      oHasher.update(sId);
    sCombinedId = oHasher.hexdigest()[:dxConfig["uMaxStackFrameHashChars"]];
    asStackFrameIds.append(sCombinedId);
    if oCdbWrapper.bGenerateReportHTML:
      asNotesHTML += ["The stack frames with ids %s and %s where combined into one id %s." % \
          (", ".join(asCombinedIds[:-1]), asCombinedIds[-1], sCombinedId)];
  oBugReport.sStackId = ".".join([s for s in asStackFrameIds]);
  # Get the bug location.
  oBugReport.sBugLocation = "(unknown)";
  for oRelevantStackFrame in aoRelevantStackFrames:
    # Find the first stack frame with an address we can show the user:
    if oRelevantStackFrame.sSimplifiedAddress:
      oBugReport.sBugLocation = oRelevantStackFrame.sSimplifiedAddress;
      if (
        oBugReport.sProcessBinaryName and (
          not oRelevantStackFrame.oModule or
          oRelevantStackFrame.oModule.sBinaryName != oBugReport.sProcessBinaryName
        )
      ):
        # Exception happened in a module, not the process' binary: add process' binary name:
        oBugReport.sBugLocation = "%s!%s" % (oBugReport.sProcessBinaryName, oBugReport.sBugLocation);
      if oRelevantStackFrame.sSourceFilePath:
        oBugReport.sBugSourceLocation = "%s @ %d" % \
            (oRelevantStackFrame.sSourceFilePath, oRelevantStackFrame.uSourceFileLineNumber);
      break;
  if oCdbWrapper.bGenerateReportHTML:
    if oBugReport.oStack.bPartialStack:
      asNotesHTML += ["There were more stack frames than shown above, but these were not considered relevant."];
    sHTML = "".join([
      asHTML      and "<ol>%s</ol>" % "".join(["<li>%s</li>" % s for s in asHTML]) or "",
      asNotesHTML and "<ul>%s</ul>" % "".join(["<li>%s</li>" % s for s in asNotesHTML]) or "",
    ]);
  else:
    sHTML = None;
  return aoRelevantStackFrames, sHTML;