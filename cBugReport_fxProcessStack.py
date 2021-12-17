import hashlib;

from .dxConfig import dxConfig;
from .SourceCodeLinks import fsb0GetSourceCodeLinkURLForPath;
from .mCP437 import fsCP437FromBytesString, fsCP437HTMLFromBytesString, fsCP437HTMLFromString;

def cBugReport_fxProcessStack(oBugReport, oCdbWrapper, oProcess, oStack):
  # Get a HTML representation of the stack, find the topmost relevant stack frame and get stack id.
  if oCdbWrapper.bGenerateReportHTML:
    asHTML = [];
    asNotesHTML = [];
  aoStackFramesPartOfId = [];
  # For recursive function loops, the frames in the loop have already been marked as part of the id, and we need to
  # check that none of them are hidden, as that makes no sense. For other exceptions, we still need to mark a few as
  # part of the id, so will need to find out which it is:
  bIdFramesHaveAlreadyBeenMarked = False;
  for oStackFrame in oStack.aoFrames:
    if oStackFrame.s0IsHiddenBecause is not None:
      assert not oStackFrame.bIsPartOfId, \
          "Cannot have a hidden frame that is part of the id";
    bIdFramesHaveAlreadyBeenMarked |= oStackFrame.bIsPartOfId;
  # If id frames have not been marked, mark as many as the default settings request. Take into account that hidden
  # frames should not be part of the id.
  if not bIdFramesHaveAlreadyBeenMarked:
    # Mark up to `uStackHashFramesCount` frames as part of the id
    uFramesToBeMarkedCount = dxConfig["uStackHashFramesCount"];
    for oStackFrame in oStack.aoFrames:
      if uFramesToBeMarkedCount == 0:
        break;
      if oStackFrame.s0IsHiddenBecause is None and oStackFrame.sId:
        oStackFrame.bIsPartOfId = True;
        uFramesToBeMarkedCount -= 1;
  
  for oStackFrame in oStack.aoFrames:
    if oCdbWrapper.bGenerateReportHTML:
      asFrameHTMLClasses = ["StackFrame"];
      asFrameNotesHTML = [];
      sOptionalSourceHTML = None;
      if oStackFrame.sb0SourceFilePath:
        sbSourceReference = b"%s%s" % (
          oStackFrame.sb0SourceFilePath,
          b"" if oStackFrame.u0SourceFileLineNumber is None else (b" @ %d" % oStackFrame.u0SourceFileLineNumber),
        );
        sb0SourceReferenceURL = fsb0GetSourceCodeLinkURLForPath(oStackFrame.sb0SourceFilePath, oStackFrame.u0SourceFileLineNumber);
        if sb0SourceReferenceURL:
          sOptionalSourceHTML = "[<a href=\"%s\" target=\"_blank\">%s</a>]" % (
            fsCP437HTMLFromBytesString(sb0SourceReferenceURL),
            fsCP437HTMLFromBytesString(sbSourceReference),
          );
        else:
          sOptionalSourceHTML = "[%s]" % fsCP437HTMLFromBytesString(sbSourceReference);
    if oCdbWrapper.bGenerateReportHTML:
      if oStackFrame.bIsInline:
        # This frame is hidden (because it is irrelevant to the crash)
          asFrameHTMLClasses.append("StackFrameInline");
          asFrameNotesHTML.append("inlined function");
      if oStackFrame.s0IsHiddenBecause is not None:
        # This frame is hidden (because it is irrelevant to the crash)
          asFrameHTMLClasses.append("StackFrameHidden");
          asFrameNotesHTML.append(fsCP437HTMLFromString(oStackFrame.s0IsHiddenBecause));
      if oStackFrame.bIsPartOfId:
          asFrameHTMLClasses.append("StackFramePartOfId");
          asFrameNotesHTML.append("id: %s" % fsCP437HTMLFromString(oStackFrame.sId));
      if not oStackFrame.o0Function:
        asFrameHTMLClasses.append("StackFrameWithoutSymbol");
        asFrameNotesHTML.append("no function symbol available");
    if oStackFrame.bIsPartOfId:
      aoStackFramesPartOfId.append(oStackFrame);
    if oCdbWrapper.bGenerateReportHTML:
      asHTML.append(" ".join([s for s in [
        "<span class=\"%s\">%s</span>" % (" ".join(asFrameHTMLClasses), fsCP437HTMLFromBytesString(oStackFrame.sbAddress)),
        asFrameNotesHTML and "<span class=\"StackFrameNotes\">(%s)</span>" % ", ".join(asFrameNotesHTML),
        sOptionalSourceHTML and "<span class=\"StackFrameSource\">[%s]</span>" % sOptionalSourceHTML,
      ] if s]));
  # Get the stack ids: one that contains all the ids for all stack frames, and one that merges stack ids to fit the
  # requested uStackHashFramesCount.
  asStackIds = [oStackFrame.sId for oStackFrame in aoStackFramesPartOfId];
  oBugReport.s0UniqueStackId = ".".join(asStackIds);
  if len(asStackIds) > dxConfig["uStackHashFramesCount"]:
    # There are too many stack hashes: concatinate all excessive hashes togerther with the last non-excessive one and
    # hash them again. This new has replaces them, bringing the number of hashes down to the maximum number. The last
    # hash is effectively a combination of all these hashes, guaranteeing a certain level of uniqueness.
    oHasher = hashlib.md5();
    while len(asStackIds) >= dxConfig["uStackHashFramesCount"]:
      oHasher.update(bytes(asStackIds.pop(), "utf-8", "strict"));
    asStackIds.append(oHasher.hexdigest()[:dxConfig["uMaxStackFrameHashChars"]]);
  oBugReport.s0StackId = ".".join(asStackIds) or None;
  # Get the bug location.
  oBugReport.s0BugLocation = "%s!(unknown)" % oProcess.sSimplifiedBinaryName;
  if aoStackFramesPartOfId:
    oTopIdStackFrame = aoStackFramesPartOfId[0];
    if oTopIdStackFrame.sb0SimplifiedAddress:
      # We can use the top stack frame for the bug locaiton.
      oBugReport.s0BugLocation = "%s%s" % (
        # We need to add the process binary only if it is not the same as the module binary for the function in which
        # the bug happened (i.e. `binary.exe!kernel32.dll!function`)
        (oProcess.sSimplifiedBinaryName + "!") if oProcess and oTopIdStackFrame.o0Module != oProcess.oMainModule
            else "",
        fsCP437FromBytesString(oTopIdStackFrame.sb0SimplifiedAddress)
      );
    if oTopIdStackFrame.sb0SourceFilePath:
      oBugReport.sBugSourceLocation = "%s%s" % (
        fsCP437FromBytesString(oTopIdStackFrame.sb0SourceFilePath),
        "" if oTopIdStackFrame.u0SourceFileLineNumber is None else " @ %d" % oTopIdStackFrame.u0SourceFileLineNumber,
      );
  if oCdbWrapper.bGenerateReportHTML:
    if oStack.bPartialStack:
      asNotesHTML += ["There were more stack frames than shown above, but these were not considered relevant."];
    sHTML = "".join([
      asHTML      and "<ol>%s</ol>" % "".join(["<li>%s</li>" % s for s in asHTML]) or "",
      asNotesHTML and "<ul>%s</ul>" % "".join(["<li>%s</li>" % s for s in asNotesHTML]) or "",
    ]);
  else:
    sHTML = None;
  return aoStackFramesPartOfId, sHTML;
