import re;

from mWindowsAPI import fsHexNumber;
from mWindowsSDK import (
  CPP_EXCEPTION_CODE,
  STATUS_ACCESS_VIOLATION,
  STATUS_BREAKPOINT,
  STATUS_FAIL_FAST_EXCEPTION,
  STATUS_FAILFAST_OOM_EXCEPTION,
  STATUS_GUARD_PAGE_VIOLATION,
  STATUS_ILLEGAL_INSTRUCTION,
  STATUS_INTEGER_DIVIDE_BY_ZERO,
  STATUS_INTEGER_OVERFLOW,
  STATUS_PRIVILEGED_INSTRUCTION,
  STATUS_SINGLE_STEP,
  STATUS_STACK_BUFFER_OVERRUN,
  STATUS_STACK_OVERFLOW,
  STATUS_STOWED_EXCEPTION,
  WRT_ORIGINATE_ERROR_EXCEPTION,
);

from mNotProvided import (
  fxGetFirstProvidedValue,
  zNotProvided,
);

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
from .cBugReport_fs0GetDisassemblyHTML import cBugReport_fs0GetDisassemblyHTML;
from .cBugReport_fs0GetMemoryDumpBlockHTML import cBugReport_fs0GetMemoryDumpBlockHTML;
from .cBugReport_fxProcessStack import cBugReport_fxProcessStack;
from .fsGetHTMLForValue import fsGetHTMLForValue;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;
from .sReportHTMLTemplate import sReportHTMLTemplate;

# Remaining local imports are at the end of this file to avoid import loops.

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
auExceptionCodesThatHappenAtTheInstructionThatTriggeredThem = [
  STATUS_ACCESS_VIOLATION,
#  STATUS_BREAKPOINT, # this one is inconsistent :(
  STATUS_ILLEGAL_INSTRUCTION,
  STATUS_INTEGER_DIVIDE_BY_ZERO,
  STATUS_INTEGER_OVERFLOW,
  STATUS_PRIVILEGED_INSTRUCTION,
  STATUS_SINGLE_STEP,
  STATUS_STACK_BUFFER_OVERRUN,
  STATUS_STACK_OVERFLOW,
];

class cBugReport(object):
  bIsInternalBug = False;
  def __init__(oSelf,
    *,
    oCdbWrapper,
    oProcess,
    oWindowsAPIThread,
    o0Exception,
    s0BugTypeId,
    s0BugDescription,
    s0SecurityImpact,
    uStackFramesCount,
  ):
    oSelf.__oCdbWrapper = oCdbWrapper;
    oSelf.__oProcess = oProcess;
    oSelf.__oWindowsAPIThread = oWindowsAPIThread;
    oSelf.__o0Exception = o0Exception;
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
    oSelf.s0BugLocation = None;
    oSelf.sBugSourceLocation = None;
    oSelf.sReportHTML = None;
  
  @property
  def o0Stack(oSelf):
    if oSelf.__o0Stack is None:
      oSelf.__o0Stack = cStack.foCreate(oSelf.__oProcess, oSelf.__oWindowsAPIThread, oSelf.uStackFramesCount);
    return oSelf.__o0Stack;
  
  def fAddMemoryDump(oSelf, uStartAddress, uEndAddress, sDescription):
#    assert uStartAddress >=0 and uStartAddress < 1 << (oSelf.__oProcess.uPointerSize * 8), \
#        "Invalid uStartAddress 0x%X." % uStartAddress;
#    assert uEndAddress >=0 and uEndAddress < 1 << (oSelf.__oProcess.uPointerSize * 8), \
#        "Invalid uEndAddress 0x%X." % uEndAddress;
    assert uEndAddress > uStartAddress, \
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
    o0BugReport = cBugReport.foCreate(
      oCdbWrapper = oCdbWrapper,
      oProcess = oProcess,
      oWindowsAPIThread = oWindowsAPIThread,
      o0Exception = oException,
      s0BugTypeId = oException.sTypeId,
      s0BugDescription = oException.sDescription,
      s0SecurityImpact = oException.s0SecurityImpact,
      uzStackFramesCount = uStackFramesCount,
    );
    if o0BugReport is None:
      return None;
    # Perform exception specific analysis:
    if oException.uCode in dfoAnalyzeException_by_uExceptionCode:
      o0BugReport = dfoAnalyzeException_by_uExceptionCode[oException.uCode](o0BugReport, oProcess, oWindowsAPIThread, oException);
      if o0BugReport is None:
        return None;
      # Apply another round of translations
      fApplyBugTranslationsToBugReport(oCdbWrapper, o0BugReport);
      if o0BugReport.s0BugTypeId is None:
        return None;
    return o0BugReport;
  
  @classmethod
  def foCreate(cClass,
    *,
    oCdbWrapper,
    oProcess,
    oWindowsAPIThread,
    o0Exception,
    s0BugTypeId,
    s0BugDescription,
    s0SecurityImpact,
    uzStackFramesCount = zNotProvided,
  ):
    uStackFramesCount = fxGetFirstProvidedValue(uzStackFramesCount, dxConfig["uMaxStackFramesCount"]);
    # Create a preliminary error report.
    oBugReport = cClass(
      oCdbWrapper = oCdbWrapper,
      oProcess = oProcess,
      oWindowsAPIThread = oWindowsAPIThread,
      o0Exception = o0Exception,
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
    assert oSelf.s0BugTypeId, \
        "Cannot report a bug with no bug type id!";
    # Calculate Stack Id, determine s0BugLocation and optionally create and return sStackHTML.
    aoStackFramesPartOfId, sStackHTML = oSelf.fxProcessStack(oCdbWrapper, oSelf.__oProcess, oSelf.__o0Stack);
    oSelf.sId = "%s %s" % (oSelf.s0BugTypeId, oSelf.s0StackId);
    
    (sbInstructionPointerName, u0InstructionPointerValue) = \
        oSelf.__oWindowsAPIThread.ftxGetInstructionPointerRegisterNameAndValue();
    if u0InstructionPointerValue is None:
      oSelf.s0Instruction = "???????? | ?? | ??? // Cannot get instruction pointer %s value for unknown reasons" % (
        str(sbInstructionPointerName, "ascii", "strict")
      );
    else:
      if oSelf.__o0Exception and oSelf.__o0Exception.uCode in auExceptionCodesThatHappenAtTheInstructionThatTriggeredThem:
        o0Instruction = oSelf.__oProcess.fo0GetInstructionForAddress(u0InstructionPointerValue);
      else:
        o0Instruction = oSelf.__oProcess.fo0GetInstructionBeforeAddress(u0InstructionPointerValue);
      if o0Instruction is not None:
        oSelf.s0Instruction = str(o0Instruction);
      else:
        o0VirtualAllocation = oSelf.__oProcess.fo0GetVirtualAllocationForAddress(u0InstructionPointerValue);
        sRemark = (
          "memory allocation information not available" if not o0VirtualAllocation else
          "not a valid address" if not o0VirtualAllocation.bIsValid else
          "no memory allocated" if o0VirtualAllocation.bFree else
          "reserved but not allocated" if o0VirtualAllocation.bReserved else
          "guard page" if o0VirtualAllocation.bGuard else
          ("Cannot disassemble %s for unknown reasons" % str(o0VirtualAllocation))
        );
        oSelf.s0Instruction = "%s | ?? | ??? // %s" % (
          fsHexNumber(u0InstructionPointerValue),
          sRemark
        );

    # If bug binary and main binary are not the same, gather information for both of them:
    aoRelevantModules = [oSelf.__oProcess.oMainModule];
    # Find the Module in which the bug is reported and add it to the relevant list if it's not there already.
    for oStackFrame in aoStackFramesPartOfId:
      if oStackFrame.o0Module:
        if oStackFrame.o0Module != oSelf.__oProcess.oMainModule:
          aoRelevantModules.append(oStackFrame.o0Module);
        break;
    # Add relevant binaries information to cBugReport and optionally to the HTML report.
    oSelf.asVersionInformation = [];
    for oModule in aoRelevantModules:
      # This function populates the version properties of the oModule object and returns HTML if a report is needed.
      if oModule.s0BinaryName:
        sBinaryName = oModule.s0BinaryName;
        oSelf.asVersionInformation.append("%s (%s)" % (sBinaryName, oModule.sISA));
    
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
        s0RegistersBlockHTML = oSelf.fs0GetRegistersBlockHTML(oSelf.__oProcess, oSelf.__oWindowsAPIThread);
        if s0RegistersBlockHTML:
          asBlocksHTML.append(s0RegistersBlockHTML);
      
      # Add relevant memory blocks in order if needed
      for uStartAddress in sorted(oSelf.__dtxMemoryDumps.keys()):
        (uEndAddress, asDescriptions) = oSelf.__dtxMemoryDumps[uStartAddress];
        sDescription = " / ".join(asDescriptions);
        s0MemoryDumpBlockHTML = oSelf.fs0GetMemoryDumpBlockHTML(oCdbWrapper, oSelf.__oProcess, sDescription, uStartAddress, uEndAddress);
        if s0MemoryDumpBlockHTML:
          asBlocksHTML.append(s0MemoryDumpBlockHTML);
      
      # Create and add disassembly blocks if needed:
      # We disassemble to top stack frame and all stack frames part of the id.
      aoDisassembleStackFrames = aoStackFramesPartOfId[:];
      if oSelf.__o0Stack.aoFrames and oSelf.__o0Stack.aoFrames[0] not in aoDisassembleStackFrames:
        aoDisassembleStackFrames.insert(0, oSelf.__o0Stack.aoFrames[0]);
      for oFrame in aoDisassembleStackFrames:
        if oFrame.u0InstructionPointer is not None:
          s0FrameDisassemblyHTML = oSelf.fs0GetDisassemblyHTML(
            oSelf.__oProcess,
            uAddress = oFrame.u0InstructionPointer,
            s0DescriptionOfInstructionBeforeAddress = None if oFrame.uIndex == 0 else "call",
            s0DescriptionOfInstructionAtAddress = "current instruction" if oFrame.uIndex == 0 else "return address",
          );
          if s0FrameDisassemblyHTML:
            asBlocksHTML.append(sBlockHTMLTemplate % {
              "sName": "Disassembly of stack frame %d at %s" % (oFrame.uIndex + 1, fsCP437HTMLFromBytesString(oFrame.sbAddress)),
              "sCollapsed": "Collapsed",
              "sContent": "<span class=\"Disassembly\">%s</span>" % s0FrameDisassemblyHTML,
            });
      
      # Add relevant binaries information to cBugReport and HTML report.
# Getting the integrity level has become error-prone and I don't care enough about it to find out what the issue is
# so I have disabled it.
      sOptionalIntegrityLevelHTML = "";
#      # Get process integrity level.
#      if oSelf.__oProcess.uIntegrityLevel is None:
#        sOptionalIntegrityLevelHTML = "(unknown)";
#      else:
#        sIntegrityLevel =  " ".join([s for s in [
#          {0: "Untrusted", 1: "Low", 2: "Medium", 3: "High", 4: "System"}.get(oSelf.__oProcess.uIntegrityLevel >> 12, "Unknown"),
#          "Integrity",
#          oSelf.__oProcess.uIntegrityLevel & 0x100 and "Plus",
#        ] if s]);
#        if oSelf.__oProcess.uIntegrityLevel >= 0x3000:
#          sIntegrityLevel += "; this process appears to run with elevated privileges!";
#        elif oSelf.__oProcess.uIntegrityLevel >= 0x2000:
#          sIntegrityLevel += "; this process appears to not be sandboxed!";
#        else:
#          sIntegrityLevel += "; this process appears to be sandboxed.";
#        sOptionalIntegrityLevelHTML = "<tr><td>Integrity level: </td><td>0x%X (%s)</td></tr>" % \
#            (oSelf.__oProcess.uIntegrityLevel, sIntegrityLevel);
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
      import mBugId, mProductDetails;
      o0ProductDetails = (
        mProductDetails.fo0GetProductDetailsForMainModule()
        or mProductDetails.fo0GetProductDetailsForModule(mBugId)
      );
      if o0ProductDetails:
        (sProductHeaderHTML, sProductFooterHTML) = ftsReportProductHeaderAndFooterHTML(o0ProductDetails);
        (sLicenseHeaderHTML, sLicenseFooterHTML) = ftsReportLicenseHeaderAndFooterHTML(o0ProductDetails);
      else:
        sProductHeaderHTML = sProductFooterHTML = sLicenseHeaderHTML = sLicenseFooterHTML = "";
      while asBlocksHTML:
        bReportTruncated = False;
        try:
          oSelf.sReportHTML = sReportHTMLTemplate % {
            "sId": fsCP437HTMLFromString(oSelf.sId),
            "sOptionalUniqueStackId": (
              "<tr><td>Full stack id:</td><td>%s</td></tr>" % fsCP437HTMLFromString(oSelf.s0UniqueStackId)
                  if oSelf.s0UniqueStackId and oSelf.s0UniqueStackId != oSelf.s0StackId else
              "<!-- unique stack id not available -->" if not oSelf.s0UniqueStackId else
              "<!-- unique stack id is the same as the regular stack id -->"
            ),
            "sBugLocation": (
              fsCP437HTMLFromString(oSelf.s0BugLocation)
                  if oSelf.s0BugLocation else
              "Unknown"
            ),
            "sBugDescription": fsCP437HTMLFromString(oSelf.s0BugDescription), # Cannot be None at this point
            "sOptionalSource": (
              "<tr><td>Source: </td><td>%s</td></tr>" % fsCP437HTMLFromString(oSelf.sBugSourceLocation)
                  if oSelf.sBugSourceLocation else
              "<!-- Source code informationn not available -->"
            ),
            "sOptionalInstruction": (
              "<tr><td>Instruction: </td><td>%s</td></tr>" % fsCP437HTMLFromString(oSelf.s0Instruction)
                  if oSelf.s0Instruction else
              "<!-- Instruction not applicable or not available -->"
            ),
            "sSecurityImpact": (
              '<span class="SecurityImpact">%s</span>' % fsCP437HTMLFromString(oSelf.s0SecurityImpact)
                  if oSelf.s0SecurityImpact is not None else
              "None"
            ),
            "sOptionalIntegrityLevel": sOptionalIntegrityLevelHTML,
            "sOptionalMemoryUsage": sOptionalMemoryUsageHTML or "",
            "sOptionalApplicationArguments": (
              "<tr><td>Arguments: </td><td>%s</td></tr>" % oCdbWrapper.asApplicationArguments
                  if oCdbWrapper.asApplicationArguments else
              "<!-- no application arguments given -->"
            ),
            "sBlocks": "\n".join(asBlocksHTML) + (
              "\n<hr/>\nThe report was truncated because there was not enough memory available to add all information available."
                  if bReportTruncated else
                ""
            ),
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
    oSelf.sProcessBinaryName = oSelf.__oProcess.sBinaryName;
    
    assert oCdbWrapper.fbFireCallbacks("Bug report", oSelf), \
        "You really should add an event handler for \"Bug report\" events, as reporting bugs is cBugIds purpose";
  
  fs0GetRegistersBlockHTML = cBugReport_fs0GetRegistersBlockHTML;
  fs0GetMemoryDumpBlockHTML = cBugReport_fs0GetMemoryDumpBlockHTML;
  fs0GetDisassemblyHTML = cBugReport_fs0GetDisassemblyHTML;
  fxProcessStack = cBugReport_fxProcessStack;
  @staticmethod
  def fsGetHTMLForValue(*txArguments, **dxArguments):
    return fsGetHTMLForValue(*txArguments, **dxArguments);
  sBlockHTMLTemplate = sBlockHTMLTemplate;


from ..mBugTranslations import fApplyBugTranslationsToBugReport;
from ..mCP437 import fsCP437HTMLFromBytesString, fsCP437HTMLFromString;
from ..mStack import cStack;
from ..dxConfig import dxConfig;
from ..ftsReportLicenseHeaderAndFooterHTML import ftsReportLicenseHeaderAndFooterHTML;
from ..ftsReportProductHeaderAndFooterHTML import ftsReportProductHeaderAndFooterHTML;
