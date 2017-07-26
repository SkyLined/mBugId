import re;
from BugTranslations import fApplyBugTranslationsToBugReport;
from cBugReport_foAnalyzeException_Cpp import cBugReport_foAnalyzeException_Cpp;
from cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION import cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION;
from cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION import cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION;
from cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION import cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION;
from cBugReport_foAnalyzeException_STATUS_NO_MEMORY import cBugReport_foAnalyzeException_STATUS_NO_MEMORY;
from cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN import cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN;
from cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW import cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW;
from cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION import cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION;
from cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION import cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION;
from cBugReport_fsGetDisassemblyHTML import cBugReport_fsGetDisassemblyHTML;
from cBugReport_fsMemoryDumpHTML import cBugReport_fsMemoryDumpHTML;
from cBugReport_fxProcessStack import cBugReport_fxProcessStack;
from cException import cException;
from cStack import cStack;
from dxConfig import dxConfig;
from FileSystem import FileSystem;
from NTSTATUS import *;
from HRESULT import *;
from sBlockHTMLTemplate import sBlockHTMLTemplate;
from oVersionInformation import oVersionInformation;
from sReportHTMLTemplate import sReportHTMLTemplate;

dfoAnalyzeException_by_uExceptionCode = {
  CPP_EXCEPTION_CODE:  cBugReport_foAnalyzeException_Cpp,
  STATUS_ACCESS_VIOLATION: cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION,
  STATUS_FAIL_FAST_EXCEPTION: cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION,
  STATUS_FAILFAST_OOM_EXCEPTION: cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION,
  STATUS_NO_MEMORY: cBugReport_foAnalyzeException_STATUS_NO_MEMORY,
  STATUS_STACK_BUFFER_OVERRUN: cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN,
  STATUS_STACK_OVERFLOW: cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW,
  STATUS_STOWED_EXCEPTION: cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION,
  WRT_ORIGINATE_ERROR_EXCEPTION: cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION,
};
class cBugReport(object):
  def __init__(oBugReport, oProcess, sBugTypeId, sBugDescription, sSecurityImpact, uStackFramesCount):
    oBugReport.oProcess = oProcess;
    oBugReport.sBugTypeId = sBugTypeId;
    oBugReport.sBugDescription = sBugDescription;
    oBugReport.sSecurityImpact = sSecurityImpact;
    oBugReport.uStackFramesCount = uStackFramesCount;
    oBugReport.__oStack = None;
    oBugReport.atxMemoryRemarks = [];
    oBugReport.__dtxMemoryDumps = {};
    oBugReport.bRegistersRelevant = True; # Set to false if register contents are not relevant to the crash
    
    if oProcess.oCdbWrapper.bGenerateReportHTML:
      oBugReport.sImportantOutputHTML = oProcess.oCdbWrapper.sImportantOutputHTML;
    oBugReport.asExceptionSpecificBlocksHTML = [];
    # This information is gathered later, when it turns out this bug needs to be reported:
    oBugReport.sStackId = None;
    oBugReport.sId = None;
    oBugReport.sBugLocation = None;
    oBugReport.sBugSourceLocation = None;
    oBugReport.sReportHTML = None;
  
  @property
  def oStack(oBugReport):
    if oBugReport.__oStack is None:
      oBugReport.__oStack = cStack.foCreate(oBugReport.oProcess, oBugReport.uStackFramesCount);
    return oBugReport.__oStack;
  
  def fAddMemoryDump(oBugReport, uStartAddress, uEndAddress, sDescription):
    assert uStartAddress not in oBugReport.__dtxMemoryDumps, \
        "Trying to dump the same memory twice";
    assert uStartAddress < uEndAddress, \
        "Cannot dump a memory region with its start address 0x%X beyond its end address 0x%X" % (uStartAddress, uEndAddress);
    uSize = uEndAddress - uStartAddress;
    assert uSize <= dxConfig["uMaxMemoryDumpSize"], \
        "Cannot dump a memory region with its end address 0x%X %d bytes beyond its start address 0x%X" % (uEndAddress, uSize, uStartAddress);
    oBugReport.__dtxMemoryDumps[uStartAddress] = (uEndAddress, sDescription);
  
  @classmethod
  def foCreateForException(cBugReport, oCdbWrapper, uExceptionCode, sExceptionDescription, bApplicationCannotHandleException):
    uStackFramesCount = dxConfig["uMaxStackFramesCount"];
    if uExceptionCode == STATUS_STACK_OVERFLOW:
      # In order to detect a recursion loop, we need more stack frames:
      uStackFramesCount += (dxConfig["uMinStackRecursionLoops"] + 1) * dxConfig["uMaxStackRecursionLoopSize"];
    oException = cException.foCreate(oCdbWrapper, uExceptionCode, sExceptionDescription, bApplicationCannotHandleException);
    # If this exception was not caused by the application, but by cdb itself, None is return. This is not a bug.
    if oException is None: return None;
    # Create a preliminary error report.
    oBugReport = cBugReport(
      oProcess = oCdbWrapper.oCurrentProcess,
      sBugTypeId = oException.sTypeId,
      sBugDescription = oException.sDescription,
      sSecurityImpact = oException.sSecurityImpact,
      uStackFramesCount = uStackFramesCount,
    );
    # Apply the first round of translations
    fApplyBugTranslationsToBugReport(oBugReport);
    # Perform exception specific analysis:
    if oException.uCode in dfoAnalyzeException_by_uExceptionCode:
      oBugReport = dfoAnalyzeException_by_uExceptionCode[oException.uCode](oBugReport, oCdbWrapper, oException);
      # Apply another round of translations
      fApplyBugTranslationsToBugReport(oBugReport);
    return oBugReport;
  
  @classmethod
  def foCreate(cBugReport, oCdbWrapper, sBugTypeId, sBugDescription, sSecurityImpact):
    uStackFramesCount = dxConfig["uMaxStackFramesCount"];
    # Create a preliminary error report.
    oBugReport = cBugReport(
      oProcess = oCdbWrapper.oCurrentProcess,
      sBugTypeId = sBugTypeId,
      sBugDescription = sBugDescription,
      sSecurityImpact = sSecurityImpact,
      uStackFramesCount = uStackFramesCount,
    );
    fApplyBugTranslationsToBugReport(oBugReport);
    return oBugReport;
  
  def fPostProcess(oBugReport, oCdbWrapper):
    # Calculate sStackId, determine sBugLocation and optionally create and return sStackHTML.
    aoStackFramesPartOfId, sStackHTML = cBugReport_fxProcessStack(oBugReport, oCdbWrapper);
    oBugReport.sId = "%s %s" % (oBugReport.sBugTypeId, oBugReport.sStackId);
    if oBugReport.sSecurityImpact is None:
      oBugReport.sSecurityImpact = "Denial of Service";
    
    # If bug binary and main binary are not the same, gather information for both of them:
    aoRelevantModules = [oBugReport.oProcess.oMainModule];
    # Find the Module in which the bug is reported and add it to the relevant list if it's not there already.
    for oStackFrame in aoStackFramesPartOfId:
      if oStackFrame.oModule:
        if oStackFrame.oModule != oBugReport.oProcess.oMainModule:
          aoRelevantModules.append(oStackFrame.oModule);
        break;
    # Add relevant binaries information to cBugReport and optionally to the HTML report.
    if oCdbWrapper.bGenerateReportHTML:
      # If a HTML report is requested, these will be used later on to construct it.
      asBinaryInformationHTML = [];
      asBinaryVersionHTML = [];
    oBugReport.asVersionInformation = [];
    for oModule in aoRelevantModules:
      # This function populates the version properties of the oModule object and returns HTML if a report is needed.
      oBugReport.asVersionInformation.append(
          "%s %s (%s)" % (oModule.sBinaryName, oModule.sFileVersion or oModule.sTimestamp or "unknown", oModule.sISA));
      if oCdbWrapper.bGenerateReportHTML:
        asBinaryInformationHTML.append(oModule.sInformationHTML);
        asBinaryVersionHTML.append("<b>%s</b>: %s (%s)" % \
            (oModule.sBinaryName, oModule.sFileVersion or oModule.sTimestamp or "unknown", oModule.sISA));
    
    if oCdbWrapper.bGenerateReportHTML:
      # Create HTML details
      asBlocksHTML = [];
      # Create and add important output block if needed
      if oBugReport.sImportantOutputHTML:
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Potentially important application output",
          "sCollapsed": "Collapsible", # ...but not Collapsed
          "sContent": oBugReport.sImportantOutputHTML,
        });
      
      # Add stack block
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Stack",
        "sCollapsed": "Collapsible", # ...but not Collapsed
        "sContent": "<span class=\"Stack\">%s</span>" % sStackHTML
      });
      
      # Add exception specific blocks if needed:
      asBlocksHTML += oBugReport.asExceptionSpecificBlocksHTML;
      
      if oBugReport.bRegistersRelevant:
        # Create and add registers block
        asRegisters = oCdbWrapper.fasExecuteCdbCommand(
          sCommand = "rM 0x%X;" % (0x1 + 0x4 + 0x8 + 0x10 + 0x20 + 0x40),
          sComment = "Get register information",
          bOutputIsInformative = True,
        );
        sRegistersHTML = "<br/>".join([oCdbWrapper.fsHTMLEncode(s, uTabStop = 8) for s in asRegisters]);
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Registers",
          "sCollapsed": "Collapsed",
          "sContent": "<span class=\"Registers\">%s</span>" % sRegistersHTML,
        });
      
      # Add relevant memory blocks in order if needed
      for uStartAddress in sorted(oBugReport.__dtxMemoryDumps.keys()):
        (uEndAddress, sDescription) = oBugReport.__dtxMemoryDumps[uStartAddress];
        sMemoryDumpHTML = cBugReport_fsMemoryDumpHTML(oBugReport, oCdbWrapper, sDescription, uStartAddress, uEndAddress)
        if sMemoryDumpHTML:
          asBlocksHTML.append(sBlockHTMLTemplate % {
            "sName": sDescription,
            "sCollapsed": "Collapsed",
            "sContent": "<span class=\"Memory\">%s</span>" % sMemoryDumpHTML,
          });
      
      # Create and add disassembly blocks if needed:
      for oFrame in aoStackFramesPartOfId:
        if oFrame.uIndex == 0:
          sBeforeAddressInstructionDescription = None;
          sAtAddressInstructionDescription = "current instruction";
        else:
          sBeforeAddressInstructionDescription = "call";
          sAtAddressInstructionDescription = "return address";
        sFrameDisassemblyHTML = cBugReport_fsGetDisassemblyHTML(oBugReport, oCdbWrapper, oFrame.uInstructionPointer, \
            sBeforeAddressInstructionDescription, sAtAddressInstructionDescription);
        if sFrameDisassemblyHTML:
          asBlocksHTML.append(sBlockHTMLTemplate % {
            "sName": "Disassembly of stack frame %d at %s" % (oFrame.uIndex + 1, oFrame.sAddress),
            "sCollapsed": "Collapsed",
            "sContent": "<span class=\"Disassembly\">%s</span>" % sFrameDisassemblyHTML,
          });
      
      # Add relevant binaries information to cBugReport and HTML report.
      sBinaryInformationHTML = "<br/><br/>".join(asBinaryInformationHTML);
      sBinaryVersionHTML = "<br/>".join(asBinaryVersionHTML) or "not available";
      if sBinaryInformationHTML:
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Binary information",
          "sCollapsed": "Collapsed",
          "sContent": "<span class=\"BinaryInformation\">%s</span>" % sBinaryInformationHTML
        });
      # Get process integrity level.
      if oBugReport.oProcess.uIntegrityLevel is None:
        sOptionalIntegrityLevelHTML = "(unknown)";
      else:
        sIntegrityLevel =  " ".join([s for s in [
          {0: "Untrusted", 1: "Low", 2: "Medium", 3: "High", 4: "System"}.get(oBugReport.oProcess.uIntegrityLevel >> 12, "Unknown"),
          "Integrity",
          oBugReport.oProcess.uIntegrityLevel & 0x100 and "Plus",
        ] if s]);
        if oBugReport.oProcess.uIntegrityLevel >= 0x3000:
          sIntegrityLevel += "; this process appears to run with elevated privileges!";
        elif oBugReport.oProcess.uIntegrityLevel >= 0x2000:
          sIntegrityLevel += "; this process appears to not be sandboxed!";
        else:
          sIntegrityLevel += "; this process appears to be sandboxed.";
        sOptionalIntegrityLevelHTML = "<tr><td>Integrity level: </td><td>0x%X (%s)</td></tr>" % \
            (oBugReport.oProcess.uIntegrityLevel, sIntegrityLevel);
      # Add Cdb IO to HTML report
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application and cdb output log",
        "sCollapsed": "Collapsed",
        "sContent": oCdbWrapper.sCdbIOHTML,
      });
      # Create the report using all available information, or a limit amount of information if there is not enough
      # memory to do that.
      while asBlocksHTML:
        bReportTruncated = False;
        try:
          oBugReport.sReportHTML = sReportHTMLTemplate % {
            "sId": oCdbWrapper.fsHTMLEncode(oBugReport.sId),
            "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation),
            "sBugDescription": oCdbWrapper.fsHTMLEncode(oBugReport.sBugDescription),
            "sBinaryVersion": sBinaryVersionHTML,
            "sOptionalSource": oBugReport.sBugSourceLocation and \
                "<tr><td>Source: </td><td>%s</td></tr>" % oBugReport.sBugSourceLocation or "",
            "sSecurityImpact": (oBugReport.sSecurityImpact == "Denial of Service" and
                "%s" or '<span class="SecurityImpact">%s</span>') % oCdbWrapper.fsHTMLEncode(oBugReport.sSecurityImpact),
            "sOptionalIntegrityLevel": sOptionalIntegrityLevelHTML,
            "sOptionalApplicationArguments": oCdbWrapper.asApplicationArguments and \
                "<tr><td>Arguments: </td><td>%s</td></tr>" % oCdbWrapper.asApplicationArguments or "",
            "sBlocks": "\r\n".join(asBlocksHTML) + 
                (bReportTruncated and "\r\n<hr/>The report was truncated because there was not enough memory available to add all information available." or ""),
            "sBugIdVersion": oVersionInformation.sCurrentVersion,
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
        oBugReport.sReportHTML = "The report was <b>NOT</b> created because there was not enough memory available to add any information.";
    # Remove the process object from the bug report and add the process binary name; we only provide basic types.
    oBugReport.sProcessBinaryName = oBugReport.oProcess.sBinaryName;
    del oBugReport.oProcess;
    
    # See if a dump should be saved
    if dxConfig["bSaveDump"]:
      # We'd like a dump file name base on the BugId, but the later may contain characters that are not valid in a file name
      sDesiredDumpFileName = "%s @ %s.dmp" % (oBugReport.sId, oBugReport.sBugLocation);
      # Thus, we need to translate these characters to create a valid filename that looks very similar to the BugId. 
      # Unfortunately, we cannot use Unicode as the communication channel with cdb is ASCII.
      sValidDumpFileName = FileSystem.fsValidName(sDesiredDumpFileName, bUnicode = False);
      if len(dxConfig["sDumpPath"])!=0:
        sValidDumpFileName = dxConfig["sDumpPath"]+sValidDumpFileName
      sOverwriteFlag = dxConfig["bOverwriteDump"] and "/o" or "";
      sMiniOptions = dxConfig["sMiniOptions"];
      oCdbWrapper.fasExecuteCdbCommand( \
        sCommand = ".dump %s /%s \"%s\";" % (sOverwriteFlag, sMiniOptions, sValidDumpFileName),
        sComment = "Save dump to file",
      );
