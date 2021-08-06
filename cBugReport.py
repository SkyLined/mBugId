import re;

import mProductDetails;
from mWindowsSDK import *;

from .cBugReport_foAnalyzeException_Cpp import cBugReport_foAnalyzeException_Cpp;
from .cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION import cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION;
from .cBugReport_foAnalyzeException_STATUS_BREAKPOINT import cBugReport_foAnalyzeException_STATUS_BREAKPOINT;
from .cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION import cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION;
from .cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION import cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION;
from .cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN import cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN;
from .cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW import cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW;
from .cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION import cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION;
from .cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION import cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION;

from .cBugReport_fs0GetRegistersBlockHTML import cBugReport_fs0GetRegistersBlockHTML;
from .cBugReport_fsGetDisassemblyHTML import cBugReport_fsGetDisassemblyHTML;
from .cBugReport_fs0GetMemoryDumpBlockHTML import cBugReport_fs0GetMemoryDumpBlockHTML;
from .cBugReport_fxProcessStack import cBugReport_fxProcessStack;
# Remaining local modules are load JIT to mitigate loops.

dfoAnalyzeException_by_uExceptionCode = {
  CPP_EXCEPTION_CODE:  cBugReport_foAnalyzeException_Cpp,
  STATUS_ACCESS_VIOLATION: cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION,
  STATUS_BREAKPOINT: cBugReport_foAnalyzeException_STATUS_BREAKPOINT,
  STATUS_FAIL_FAST_EXCEPTION: cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION,
  STATUS_FAILFAST_OOM_EXCEPTION: cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION,
  STATUS_GUARD_PAGE_VIOLATION: cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION, # Special type of AV
  STATUS_STACK_BUFFER_OVERRUN: cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN,
  STATUS_STACK_OVERFLOW: cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW,
  STATUS_STOWED_EXCEPTION: cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION,
  WRT_ORIGINATE_ERROR_EXCEPTION: cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION,
};
class cBugReport(object):
  def __init__(oSelf, oCdbWrapper, oProcess, oWindowsAPIThread, s0BugTypeId, s0BugDescription, s0SecurityImpact, uStackFramesCount):
    oSelf.__oCdbWrapper = oCdbWrapper;
    oSelf.__oProcess = oProcess;
    oSelf.__oWindowsAPIThread = oWindowsAPIThread;
    oSelf.s0BugTypeId = s0BugTypeId;
    oSelf.s0BugDescription = s0BugDescription;
    oSelf.s0SecurityImpact = s0SecurityImpact;
    oSelf.uStackFramesCount = uStackFramesCount;
    oSelf.__o0Stack = None;
    oSelf.atxMemoryRemarks = [];
    oSelf.__dtxMemoryDumps = {};
    oSelf.bRegistersRelevant = True; # Set to false if register contents are not relevant to the crash
    
    oSelf.asExceptionSpecificBlocksHTML = [];
    # This information is gathered later, when it turns out this bug needs to be reported:
    oSelf.s0StackId = None;
    oSelf.s0UniqueStackId = None;
    oSelf.sId = None;
    oSelf.sBugLocation = None;
    oSelf.sBugSourceLocation = None;
    oSelf.sReportHTML = None;
  
  @property
  def o0Stack(oSelf):
    if oSelf.__o0Stack is None:
      oSelf.__o0Stack = cStack.foCreate(oSelf.__oProcess, oSelf.__oWindowsAPIThread, oSelf.uStackFramesCount);
    return oSelf.__o0Stack;
  
  def fAddMemoryDump(oSelf, uStartAddress, uEndAddress, sDescription):
    assert uStartAddress < uEndAddress, \
        "Cannot dump a memory region with its start address 0x%X beyond its end address 0x%X" % (uStartAddress, uEndAddress);
    uSize = uEndAddress - uStartAddress;
    assert uSize <= dxConfig["uMaxMemoryDumpSize"], \
        "Cannot dump a memory region with its end address 0x%X %d bytes beyond its start address 0x%X" % (uEndAddress, uSize, uStartAddress);
    if uStartAddress in oSelf.__dtxMemoryDumps:
      # If it already exists, expand it to the new end address if needed and
      # add the description if different.
      (uPreviousEndAddress, asDescriptions) = oSelf.__dtxMemoryDumps[uStartAddress];
      if sDescription not in asDescriptions:
        asDescriptions.append(sDescription);
      if uPreviousEndAddress > uEndAddress:
        uEndAddress = uPreviousEndAddress;
    else:
      asDescriptions = [sDescription];
    oSelf.__dtxMemoryDumps[uStartAddress] = (uEndAddress, asDescriptions);
  
  @classmethod
  def fo0CreateForException(cBugReport, oCdbWrapper, oProcess, oWindowsAPIThread, oException):
    uStackFramesCount = dxConfig["uMaxStackFramesCount"];
    if oException.uCode == STATUS_STACK_OVERFLOW:
      # In order to detect a recursion loop, we need more stack frames:
      uStackFramesCount += (dxConfig["uMinStackRecursionLoops"] + 1) * dxConfig["uMaxStackRecursionLoopSize"];
    # If this exception was not caused by the application, but by cdb itself, None is return. This is not a bug.
    # Create a preliminary error report.
    oBugReport = cBugReport(
      oCdbWrapper = oCdbWrapper,
      oProcess = oProcess,
      oWindowsAPIThread = oWindowsAPIThread,
      s0BugTypeId = oException.sTypeId,
      s0BugDescription = oException.sDescription,
      s0SecurityImpact = oException.s0SecurityImpact,
      uStackFramesCount = uStackFramesCount,
    );
    # Apply the first round of translations
    fApplyBugTranslationsToBugReport(oCdbWrapper, oBugReport);
    if oBugReport.s0BugTypeId is None:
      return None;
    # Perform exception specific analysis:
    if oException.uCode in dfoAnalyzeException_by_uExceptionCode:
      oBugReport = dfoAnalyzeException_by_uExceptionCode[oException.uCode](oBugReport, oProcess, oWindowsAPIThread, oException);
      if oBugReport is None:
        return None;
      # Apply another round of translations
      fApplyBugTranslationsToBugReport(oCdbWrapper, oBugReport);
      if oBugReport.s0BugTypeId is None:
        return None;
    return oBugReport;
  
  @classmethod
  def foCreate(cBugReport, oCdbWrapper, oProcess, oWindowsAPIThread, s0BugTypeId, s0BugDescription, s0SecurityImpact):
    uStackFramesCount = dxConfig["uMaxStackFramesCount"];
    # Create a preliminary error report.
    oBugReport = cBugReport(
      oCdbWrapper = oCdbWrapper,
      oProcess = oProcess,
      oWindowsAPIThread = oWindowsAPIThread,
      s0BugTypeId = s0BugTypeId,
      s0BugDescription = s0BugDescription,
      s0SecurityImpact = s0SecurityImpact,
      uStackFramesCount = uStackFramesCount,
    );
    fApplyBugTranslationsToBugReport(oCdbWrapper, oBugReport);
    if oBugReport.s0BugTypeId is None:
      return None;
    return oBugReport;
  
  def fReport(oSelf):
    oCdbWrapper = oSelf.__oCdbWrapper
    import mBugId;
    assert oSelf.s0BugTypeId, \
        "Cannot report a bug with no bug type id!";
    # Remove the internal process object from the bug report; it is no longer needed and should not be exposed to the
    # outside.
    oProcess = oSelf.__oProcess;
    del oSelf.__oProcess;
    oWindowsAPIThread = oSelf.__oWindowsAPIThread;
    del oSelf.__oWindowsAPIThread;
    o0Stack = oSelf.__o0Stack;
#    del oSelf.__o0Stack;
    # Calculate Stack Id, determine sBugLocation and optionally create and return sStackHTML.
    aoStackFramesPartOfId, sStackHTML = oSelf.fxProcessStack(oCdbWrapper, oProcess, o0Stack);
    oSelf.sId = "%s %s" % (oSelf.s0BugTypeId, oSelf.s0StackId);
    
    # If bug binary and main binary are not the same, gather information for both of them:
    aoRelevantModules = [oProcess.oMainModule];
    # Find the Module in which the bug is reported and add it to the relevant list if it's not there already.
    for oStackFrame in aoStackFramesPartOfId:
      if oStackFrame.o0Module:
        if oStackFrame.o0Module != oProcess.oMainModule:
          aoRelevantModules.append(oStackFrame.o0Module);
        break;
    # Add relevant binaries information to cBugReport and optionally to the HTML report.
    if oCdbWrapper.bGenerateReportHTML:
      # If a HTML report is requested, these will be used later on to construct it.
      asBinaryInformationHTML = [];
      asBinaryVersionHTML = [];
    oSelf.asVersionInformation = [];
    for oModule in aoRelevantModules:
      # This function populates the version properties of the oModule object and returns HTML if a report is needed.
      if oModule.sb0BinaryName:
        sBinaryName = str(oModule.sb0BinaryName, 'latin1');
        sVersion = str(oModule.sb0FileVersion or oModule.sb0Timestamp or b"unknown", 'latin1');
        oSelf.asVersionInformation.append("%s %s (%s)" % (sBinaryName, sVersion, oModule.sISA));
        if oCdbWrapper.bGenerateReportHTML:
          asBinaryInformationHTML.append(oModule.sInformationHTML);
          asBinaryVersionHTML.append("<b>%s</b>: %s (%s)" % (sBinaryName, sVersion, oModule.sISA));
    
    if oCdbWrapper.bGenerateReportHTML:
      # Create HTML details
      asBlocksHTML = [];
      # Create and add important output block if needed
      if oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Application run log",
          "sCollapsed": "Collapsible", # ...but not Collapsed
          "sContent": oCdbWrapper.sLogHTML,
        });
      
      # Add stack block
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Stack",
        "sCollapsed": "Collapsible", # ...but not Collapsed
        "sContent": "<span class=\"Stack\">%s</span>" % sStackHTML
      });
      
      # Add exception specific blocks if needed:
      asBlocksHTML += oSelf.asExceptionSpecificBlocksHTML;
      
      # Add registers if needed
      if oSelf.bRegistersRelevant:
        s0RegistersBlockHTML = oSelf.fs0GetRegistersBlockHTML(oProcess, oWindowsAPIThread);
        if s0RegistersBlockHTML:
          asBlocksHTML.append(s0RegistersBlockHTML);
      
      # Add relevant memory blocks in order if needed
      for uStartAddress in sorted(oSelf.__dtxMemoryDumps.keys()):
        (uEndAddress, asDescriptions) = oSelf.__dtxMemoryDumps[uStartAddress];
        sDescription = " / ".join(asDescriptions);
        s0MemoryDumpBlockHTML = oSelf.fs0GetMemoryDumpBlockHTML(oCdbWrapper, oProcess, sDescription, uStartAddress, uEndAddress);
        if s0MemoryDumpBlockHTML:
          asBlocksHTML.append(s0MemoryDumpBlockHTML);
      
      # Create and add disassembly blocks if needed:
      for oFrame in aoStackFramesPartOfId:
        if oFrame.u0InstructionPointer is not None:
          if oFrame.uIndex == 0:
            sFrameDisassemblyHTML = oSelf.fsGetDisassemblyHTML(
              oCdbWrapper,
              oProcess,
              uAddress = oFrame.u0InstructionPointer,
              sDescriptionOfInstructionAtAddress = "current instruction"
            );
          else:
            sFrameDisassemblyHTML = oSelf.fsGetDisassemblyHTML(
              oCdbWrapper, 
              oProcess,
              uAddress = oFrame.u0InstructionPointer,
              sDescriptionOfInstructionBeforeAddress = "call",
              sDescriptionOfInstructionAtAddress = "return address"
            );
          if sFrameDisassemblyHTML:
            asBlocksHTML.append(sBlockHTMLTemplate % {
              "sName": "Disassembly of stack frame %d at %s" % (oFrame.uIndex + 1, oCdbWrapper.fsHTMLEncode(oFrame.sbAddress)),
              "sCollapsed": "Collapsed",
              "sContent": "<span class=\"Disassembly\">%s</span>" % sFrameDisassemblyHTML,
            });
      
      # Add relevant binaries information to cBugReport and HTML report.
      sBinaryInformationHTML = "<br/>\n<br/>\n".join(asBinaryInformationHTML);
      sBinaryVersionHTML = "<br/>\n".join(asBinaryVersionHTML) or "not available";
      if sBinaryInformationHTML:
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Binary information",
          "sCollapsed": "Collapsed",
          "sContent": "<span class=\"BinaryInformation\">%s</span>" % sBinaryInformationHTML
        });
# Getting the integrity level has become error-prone and I don't care enough about it to find out what the issue is
# so I have disabled it.
      sOptionalIntegrityLevelHTML = "";
#      # Get process integrity level.
#      if oProcess.uIntegrityLevel is None:
#        sOptionalIntegrityLevelHTML = "(unknown)";
#      else:
#        sIntegrityLevel =  " ".join([s for s in [
#          {0: "Untrusted", 1: "Low", 2: "Medium", 3: "High", 4: "System"}.get(oProcess.uIntegrityLevel >> 12, "Unknown"),
#          "Integrity",
#          oProcess.uIntegrityLevel & 0x100 and "Plus",
#        ] if s]);
#        if oProcess.uIntegrityLevel >= 0x3000:
#          sIntegrityLevel += "; this process appears to run with elevated privileges!";
#        elif oProcess.uIntegrityLevel >= 0x2000:
#          sIntegrityLevel += "; this process appears to not be sandboxed!";
#        else:
#          sIntegrityLevel += "; this process appears to be sandboxed.";
#        sOptionalIntegrityLevelHTML = "<tr><td>Integrity level: </td><td>0x%X (%s)</td></tr>" % \
#            (oProcess.uIntegrityLevel, sIntegrityLevel);
      if oCdbWrapper.oJobObject is None or oSelf.s0BugTypeId != "OOM":
        sOptionalMemoryUsageHTML = None;
      else:
        sOptionalMemoryUsageHTML = "<tr><td>Memory usage: </td><td>%6.1fMb (process)/ %6.1fMb (application)</td></tr>" % (
          oCdbWrapper.oJobObject.fuGetMaxProcessMemoryUse() / 1000000,
          oCdbWrapper.oJobObject.fuGetMaxTotalMemoryUse() / 1000000,
        );
      # Add Cdb IO to HTML report
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application and cdb output log",
        "sCollapsed": "Collapsed",
        "sContent": oCdbWrapper.sCdbIOHTML,
      });
      # Create the report using all available information, or a limit amount of information if there is not enough
      # memory to do that.
      o0ProductDetails = (
        mProductDetails.fo0GetProductDetailsForMainModule()
        or mProductDetails.fo0GetProductDetailsForModule(mBugId)
      );
      if o0ProductDetails:
        (sProductHeaderHTML, sProductFooterHTML) = ftsReportProductHeaderAndFooterHTML(o0ProductDetails);
        (sLicenseHeaderHTML, sLicenseFooterHTML) = ftsReportLicenseHeaderAndFooterHTML(o0ProductDetails);
      else:
        sProductHeaderHTML = sProductFooter = sLicenseHeaderHTML = sLicenseFooterHTML = "";
      while asBlocksHTML:
        bReportTruncated = False;
        try:
          oSelf.sReportHTML = sReportHTMLTemplate % {
            "sId": oCdbWrapper.fsHTMLEncode(oSelf.sId),
            "sOptionalUniqueStackId": oSelf.s0UniqueStackId != oSelf.s0StackId and
                "<tr><td>Full stack id:</td><td>%s</td></tr>" % oCdbWrapper.fsHTMLEncode(oSelf.s0UniqueStackId) or "",
            "sBugLocation": oCdbWrapper.fsHTMLEncode(oSelf.sBugLocation),
            "sBugDescription": oCdbWrapper.fsHTMLEncode(oSelf.s0BugDescription), # Cannot be None at this point
            "sBinaryVersion": sBinaryVersionHTML,
            "sOptionalSource": oSelf.sBugSourceLocation and \
                "<tr><td>Source: </td><td>%s</td></tr>" % oSelf.sBugSourceLocation or "",
            "sSecurityImpact": (
              "None" if oSelf.s0SecurityImpact is None
              else ('<span class="SecurityImpact">%s</span>' % oCdbWrapper.fsHTMLEncode(oSelf.s0SecurityImpact))
            ),
            "sOptionalIntegrityLevel": sOptionalIntegrityLevelHTML,
            "sOptionalMemoryUsage": sOptionalMemoryUsageHTML or "",
            "sOptionalApplicationArguments": oCdbWrapper.asApplicationArguments and \
                "<tr><td>Arguments: </td><td>%s</td></tr>" % oCdbWrapper.asApplicationArguments or "",
            "sBlocks": "\n".join(asBlocksHTML) + 
                (bReportTruncated and "\n<hr/>\nThe report was truncated because there was not enough memory available to add all information available." or ""),
            "sProductHeader": sProductHeaderHTML,
            "sProductFooter": sProductFooterHTML,
            "sLicenseHeader": sLicenseHeaderHTML,
            "sLicenseFooter": sLicenseFooterHTML,
          };
        except MemoryError:
          # We cannot add everything, so let's remove a block of information to free up some memory and reduce the size
          # of the final report before we try again. It makes sense to remove the last block, as they are ordered
          # (somewhat) by how useful the information is to the user, the last block containing less useful information
          # than the first.
          asBlocksHTML.pop();
          # Add a notice to the report about it being truncated.
          bReportTruncated = True;
        else:
          break;
      else:
        # There is so little memory available that we cannot seem to be able to create a report at all.
        # This is highly unlikely, but let's try to handle every eventuality.
        oSelf.sReportHTML = "The report was <b>NOT</b> created because there was not enough memory available to add any information.";
    oSelf.sProcessBinaryName = oProcess.sBinaryName;
    
    assert oCdbWrapper.fbFireCallbacks("Bug report", oSelf), \
        "You really should add an event handler for \"Bug report\" events, as reporting bugs is cBugIds purpose";
  
  fs0GetRegistersBlockHTML = cBugReport_fs0GetRegistersBlockHTML;
  fs0GetMemoryDumpBlockHTML = cBugReport_fs0GetMemoryDumpBlockHTML;
  fsGetDisassemblyHTML = cBugReport_fsGetDisassemblyHTML;
  fxProcessStack = cBugReport_fxProcessStack;

from .mBugTranslations import fApplyBugTranslationsToBugReport;
from .cStack import cStack;
from .dxConfig import dxConfig;
from .ftsReportLicenseHeaderAndFooterHTML import ftsReportLicenseHeaderAndFooterHTML;
from .ftsReportProductHeaderAndFooterHTML import ftsReportProductHeaderAndFooterHTML;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .sReportHTMLTemplate import sReportHTMLTemplate;
