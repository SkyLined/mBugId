import re;
from cBugReport_foAnalyzeException_Cpp import cBugReport_foAnalyzeException_Cpp;
from cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION import cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION;
from cBugReport_foAnalyzeException_STATUS_BREAKPOINT import cBugReport_foAnalyzeException_STATUS_BREAKPOINT;
from cBugReport_foAnalyzeException_STATUS_INVALID_HANDLE import cBugReport_foAnalyzeException_STATUS_INVALID_HANDLE;
from cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION import cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION;
from cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION import cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION;
from cBugReport_foAnalyzeException_STATUS_NO_MEMORY import cBugReport_foAnalyzeException_STATUS_NO_MEMORY;
from cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN import cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN;
from cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW import cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW;
from cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION import cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION;
from cBugReport_foAnalyzeException_STATUS_WX86_BREAKPOINT import cBugReport_foAnalyzeException_STATUS_WX86_BREAKPOINT;
from cBugReport_foTranslate import cBugReport_foTranslate;
from cBugReport_fsGetDisassemblyHTML import cBugReport_fsGetDisassemblyHTML;
from cBugReport_fsMemoryDumpHTML import cBugReport_fsMemoryDumpHTML;
from cBugReport_fxProcessStack import cBugReport_fxProcessStack;
from cException import cException;
from cStack import cStack;
from cProcess import cProcess;
from dxBugIdConfig import dxBugIdConfig;
from FileSystem import FileSystem;
from NTSTATUS import *;
from HRESULT import *;
from sBlockHTMLTemplate import sBlockHTMLTemplate;
from sVersion import sVersion;
from sDetailsHTMLTemplate import sDetailsHTMLTemplate;

dfoAnalyzeException_by_uExceptionCode = {
  CPP_EXCEPTION_CODE:  cBugReport_foAnalyzeException_Cpp,
  STATUS_ACCESS_VIOLATION: cBugReport_foAnalyzeException_STATUS_ACCESS_VIOLATION,
  STATUS_BREAKPOINT: cBugReport_foAnalyzeException_STATUS_BREAKPOINT,
  STATUS_INVALID_HANDLE: cBugReport_foAnalyzeException_STATUS_INVALID_HANDLE,
  STATUS_FAIL_FAST_EXCEPTION: cBugReport_foAnalyzeException_STATUS_FAIL_FAST_EXCEPTION,
  STATUS_FAILFAST_OOM_EXCEPTION: cBugReport_foAnalyzeException_STATUS_FAILFAST_OOM_EXCEPTION,
  STATUS_NO_MEMORY: cBugReport_foAnalyzeException_STATUS_NO_MEMORY,
  STATUS_STACK_BUFFER_OVERRUN: cBugReport_foAnalyzeException_STATUS_STACK_BUFFER_OVERRUN,
  STATUS_STACK_OVERFLOW: cBugReport_foAnalyzeException_STATUS_STACK_OVERFLOW,
  STATUS_STOWED_EXCEPTION: cBugReport_foAnalyzeException_STATUS_STOWED_EXCEPTION,
  STATUS_WX86_BREAKPOINT: cBugReport_foAnalyzeException_STATUS_WX86_BREAKPOINT,
};
# Hide some functions at the top of the stack that are merely helper functions and not relevant to the bug:
asHiddenTopFrames = [
  "KERNELBASE.dll!RaiseException",
  "ntdll.dll!KiUserExceptionDispatch",
  "ntdll.dll!NtRaiseException",
  "ntdll.dll!RtlDispatchException",
  "ntdll.dll!RtlpExecuteHandlerForException",
  "ntdll.dll!ZwRaiseException",
];
class cBugReport(object):
  def __init__(oBugReport, oCdbWrapper, sBugTypeId, sBugDescription, sSecurityImpact, oStack):
    oBugReport.oCdbWrapper = oCdbWrapper;
    oBugReport.sBugTypeId = sBugTypeId;
    oBugReport.sBugDescription = sBugDescription;
    oBugReport.sSecurityImpact = sSecurityImpact;
    oBugReport.oProcess = cProcess.foCreate(oCdbWrapper);
    oBugReport.oStack = oStack;
    oBugReport.atxMemoryRemarks = [];
    oBugReport.atxMemoryDumps = [];
    oBugReport.bRegistersRelevant = True; # Set to false if register contents are not relevant to the crash
    
    if oCdbWrapper.bGetDetailsHTML:
      oBugReport.sImportantOutputHTML = oCdbWrapper.sImportantOutputHTML;
    oBugReport.sProcessBinaryName = oBugReport.oProcess.sBinaryName;
    oBugReport.asExceptionSpecificBlocksHTML = [];
    # This information is gathered later, when it turns out this bug needs to be reported:
    oBugReport.sStackId = None;
    oBugReport.sId = None;
    oBugReport.sBugLocation = None;
    oBugReport.sBugSourceLocation = None;
  
  def foTranslate(oBugReport, dtxTranslations):
    return cBugReport_foTranslate(oBugReport, dtxTranslations);
  
  def fHideTopStackFrames(oBugReport, dasHiddenFrames_by_sBugTypeIdRegExp):
    for (sBugTypeIdRegExp, asHiddenFrames) in dasHiddenFrames_by_sBugTypeIdRegExp.items():
      if re.match("^(%s)$" % sBugTypeIdRegExp, oBugReport.sBugTypeId):
        oBugReport.oStack.fHideTopFrames(asHiddenFrames);
  
  @classmethod
  def foCreateForException(cBugReport, oCdbWrapper, uExceptionCode, sExceptionDescription):
    uStackFramesCount = dxBugIdConfig["uMaxStackFramesCount"];
    if uExceptionCode == STATUS_STACK_OVERFLOW:
      # In order to detect a recursion loop, we need more stack frames:
      uStackFramesCount += dxBugIdConfig["uMinStackRecursionLoops"] * dxBugIdConfig["uMaxStackRecursionLoopSize"]
    oStack = cStack.foCreate(oCdbWrapper, uStackFramesCount);
    if not oCdbWrapper.bCdbRunning: return None;
    oException = cException.foCreate(oCdbWrapper, uExceptionCode, sExceptionDescription, oStack);
    if not oCdbWrapper.bCdbRunning: return None;
    # If this exception was not caused by the application, but by cdb itself, None is return. This is not a bug.
    if oException is None: return None;
    # Hide some functions at the top of the stack that are merely helper functions and not relevant to the error:
    oStack.fHideTopFrames(asHiddenTopFrames);
    # Create a preliminary error report.
    oBugReport = cBugReport(
      oCdbWrapper = oCdbWrapper,
      sBugTypeId = oException.sTypeId,
      sBugDescription = oException.sDescription,
      sSecurityImpact = oException.sSecurityImpact,
      oStack = oStack,
    );
    
    # Perform exception specific analysis:
    foAnalyzeException = dfoAnalyzeException_by_uExceptionCode.get(oException.uCode);
    if foAnalyzeException:
      oBugReport = foAnalyzeException(oBugReport, oCdbWrapper, oException);
      if not oCdbWrapper.bCdbRunning: return None;
      if not oBugReport:
        # This exception is not a bug, continue the application.
        return None;
    return oBugReport;

  @classmethod
  def foCreate(cBugReport, oCdbWrapper, sBugTypeId, sBugDescription, sSecurityImpact):
    uStackFramesCount = dxBugIdConfig["uMaxStackFramesCount"];
    oStack = cStack.foCreate(oCdbWrapper, uStackFramesCount);
    if not oCdbWrapper.bCdbRunning: return None;
    # Hide some functions at the top of the stack that are merely helper functions and not relevant to the error:
    oStack.fHideTopFrames(asHiddenTopFrames);
    # Create a preliminary error report.
    oBugReport = cBugReport(
      oCdbWrapper = oCdbWrapper,
      sBugTypeId = sBugTypeId,
      sBugDescription = sBugDescription,
      sSecurityImpact = sSecurityImpact,
      oStack = oStack,
    );
    return oBugReport;
  
  def fPostProcess(oBugReport, oCdbWrapper):
    # Calculate sStackId, determine sBugLocation and optionally create and return sStackHTML.
    aoRelevantStackFrames, sStackHTML = cBugReport_fxProcessStack(oBugReport, oCdbWrapper);
    oBugReport.sId = "%s %s" % (oBugReport.sBugTypeId, oBugReport.sStackId);
    if oBugReport.sSecurityImpact is None:
      oBugReport.sSecurityImpact = "Denial of Service";
    
    # Find cModule for main process binary (i.e. the .exe)
    aoProcessBinaryModules = oCdbWrapper.faoGetModulesForFileNameInCurrentProcess(oBugReport.sProcessBinaryName);
    if not oCdbWrapper.bCdbRunning: return None;
    assert len(aoProcessBinaryModules) > 0, "Cannot find binary %s module" % oBugReport.sProcessBinaryName;
    # Add main process binary version information to bug report. If the binary is loaded as a module multiple times
    # in the process, the first should be the binary that was executed.
    oMainModule = aoProcessBinaryModules[0];
    
    # Find cModule for bug binary (i.e. the module in which the bug is located)
    oBugModule = aoRelevantStackFrames and aoRelevantStackFrames[0].oModule;
    # If bug niary and main binary are not the same, gather information for both of them:
    aoRelevantModules = [oMainModule];
    if oBugModule and oBugModule != oMainModule:
      aoRelevantModules.append(oBugModule);
    # Add relevant binaries information to cBugReport and optionally to the HTML report.
    if oCdbWrapper.bGetDetailsHTML: # Generate sDetailsHTML?
      # If a HTML report is requested, these will be used later on to construct it.
      asBinaryInformationHTML = [];
      asBinaryVersionHTML = [];
    oBugReport.asVersionInformation = [];
    for oModule in aoRelevantModules:
      sBinaryInformationHTML = oModule.fsGetInformationHTML(oCdbWrapper);
      if not oCdbWrapper.bCdbRunning: return None;
      if oCdbWrapper.bGetDetailsHTML: # Generate sDetailsHTML?
        asBinaryInformationHTML.append(sBinaryInformationHTML);
        asBinaryVersionHTML.append("<b>%s</b>: %s" % (oModule.sBinaryName, oModule.sFileVersion or oModule.sTimestamp or "unknown"));
      oBugReport.asVersionInformation.append(
          "%s %s" % (oModule.sBinaryName, oModule.sFileVersion or oModule.sTimestamp or "unknown"));
    
    if oCdbWrapper.bGetDetailsHTML: # Generate sDetailsHTML?
      # Create HTML details
      asBlocksHTML = [];
      # Create and add important output block if needed
      if oBugReport.sImportantOutputHTML:
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Potentially important application output",
          "sContent": oBugReport.sImportantOutputHTML,
        });
      
      # Add stack block
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Stack",
        "sContent": "<span class=\"Stack\">%s</span>" % sStackHTML
      });
      
      # Add exception specific blocks if needed:
      asBlocksHTML += oBugReport.asExceptionSpecificBlocksHTML;
      
      if oBugReport.bRegistersRelevant:
        # Create and add registers block
        asRegisters = oCdbWrapper.fasSendCommandAndReadOutput(
          "rM 0x%X; $$ Get register information" % (0x1 + 0x4 + 0x8 + 0x10 + 0x20 + 0x40),
          bOutputIsInformative = True,
        );
        if not oCdbWrapper.bCdbRunning: return None;
        sRegistersHTML = "<br/>".join([oCdbWrapper.fsHTMLEncode(s) for s in asRegisters]);
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Registers",
          "sContent": "<span class=\"Registers\">%s</span>" % sRegistersHTML,
        });
      
      # Add relevant memory blocks in order if needed
      auAddresses = set();
      for (sDescription, uStartAddress, uSize) in oBugReport.atxMemoryDumps:
        auAddresses.add(uStartAddress);
      for uAddress in sorted(list(auAddresses)):
        for (sDescription, uStartAddress, uSize) in oBugReport.atxMemoryDumps:
          if uStartAddress == uAddress:
            sMemoryDumpHTML = cBugReport_fsMemoryDumpHTML(oBugReport, oCdbWrapper, sDescription, uStartAddress, uSize)
            if not oCdbWrapper.bCdbRunning: return None;
            if sMemoryDumpHTML:
              asBlocksHTML.append(sBlockHTMLTemplate % {
                "sName": sDescription,
                "sContent": "<span class=\"Memory\">%s</span>" % sMemoryDumpHTML,
              });
      
      # Create and add disassembly blocks if needed:
      uLastInstructionPointer = None;
      for oFrame in aoRelevantStackFrames:
        # Inlined functions do not add a new location to disassemble.
        if uLastInstructionPointer != oFrame.uInstructionPointer:
          uLastInstructionPointer = oFrame.uInstructionPointer;
          uFrameNumber = oFrame.uNumber + 1; # Make it base 1, rather than 0
          if oFrame.uNumber == 0:
            sBeforeAddressInstructionDescription = None;
            sAtAddressInstructionDescription = "current instruction";
          else:
            sBeforeAddressInstructionDescription = "call";
            sAtAddressInstructionDescription = "return address";
          sFrameDisassemblyHTML = cBugReport_fsGetDisassemblyHTML(oBugReport, oCdbWrapper, oFrame.uInstructionPointer, \
              sBeforeAddressInstructionDescription, sAtAddressInstructionDescription);
          if not oCdbWrapper.bCdbRunning: return None;
          if sFrameDisassemblyHTML:
            asBlocksHTML.append(sBlockHTMLTemplate % {
              "sName": "Disassembly of stack frame %d at %s" % (uFrameNumber, oFrame.sAddress),
              "sContent": "<span class=\"Disassembly\">%s</span>" % sFrameDisassemblyHTML,
            });
      
      # Find cModule for main process binary (i.e. the .exe)
      aoProcessBinaryModules = oCdbWrapper.faoGetModulesForFileNameInCurrentProcess(oBugReport.sProcessBinaryName);
      if not oCdbWrapper.bCdbRunning: return None;
      assert len(aoProcessBinaryModules) > 0, "Cannot find binary %s module" % oBugReport.sProcessBinaryName;
      # Add main process binary version information to bug report. If the binary is loaded as a module multiple times
      # in the process, the first should be the binary that was executed.
      oMainModule = aoProcessBinaryModules[0];
      
      # Find cModule for bug binary (i.e. the module in which the bug is located)
      oBugModule = aoRelevantStackFrames and aoRelevantStackFrames[0].oModule;
      # If bug niary and main binary are not the same, gather information for both of them:
      aoRelevantModules = [oMainModule];
      if oBugModule and oBugModule != oMainModule:
        aoRelevantModules.append(oBugModule);
      # Add relevant binaries information to cBugReport and HTML report.
      sBinaryInformationHTML = "<br/><br/>".join(asBinaryInformationHTML);
      sBinaryVersionHTML = "<br/>".join(asBinaryVersionHTML) or "not available";
      if sBinaryInformationHTML:
        asBlocksHTML.append(sBlockHTMLTemplate % {
          "sName": "Binary information",
          "sContent": "<span class=\"BinaryInformation\">%s</span>" % sBinaryInformationHTML
        });
      
      # Convert saved cdb IO HTML into one string and delete everything but the last line to free up some memory.
      sCdbStdIOHTML = '<hr/>'.join(oBugReport.oCdbWrapper.asCdbStdIOBlocksHTML);
      oBugReport.oCdbWrapper.asCdbStdIOBlocksHTML = oBugReport.oCdbWrapper.asCdbStdIOBlocksHTML[-1:];
      asBlocksHTML.append(sBlockHTMLTemplate % {
        "sName": "Application and cdb output log",
        "sContent": sCdbStdIOHTML
      });
      # Stick everything together.
      oBugReport.sDetailsHTML = sDetailsHTMLTemplate % {
        "sId": oCdbWrapper.fsHTMLEncode(oBugReport.sId),
        "sBugLocation": oCdbWrapper.fsHTMLEncode(oBugReport.sBugLocation),
        "sBugDescription": oCdbWrapper.fsHTMLEncode(oBugReport.sBugDescription),
        "sBinaryVersion": sBinaryVersionHTML,
        "sOptionalSource": oBugReport.sBugSourceLocation and \
            "<tr><td>Source: </td><td>%s</td></tr>" % oBugReport.sBugSourceLocation or "",
        "sSecurityImpact": (oBugReport.sSecurityImpact == "Denial of Service" and
            "%s" or '<span class="SecurityImpact">%s</span>') % oCdbWrapper.fsHTMLEncode(oBugReport.sSecurityImpact),
        "sOptionalCommandLine": oBugReport.oCdbWrapper.asApplicationCommandLine and \
            "<tr><td>Command line: </td><td>%s</td></tr>" % oBugReport.oCdbWrapper.asApplicationCommandLine or "",
        "sBlocks": "".join(asBlocksHTML),
        "sCdbStdIO": sCdbStdIOHTML,
        "sBugIdVersion": sVersion,
      };
    
    # See if a dump should be saved
    if dxBugIdConfig["bSaveDump"]:
      # We'd like a dump file name base on the BugId, but the later may contain characters that are not valid in a file name
      sDesiredDumpFileName = "%s @ %s.dmp" % (oBugId.oBugReport.sId, oBugId.oBugReport.sBugLocation);
      # Thus, we need to translate these characters to create a valid filename that looks very similar to the BugId. 
      # Unfortunately, we cannot use Unicode as the communication channel with cdb is ASCII.
      sValidDumpFileName = FileSystem.fsValidName(sDesiredDumpFileName, bUnicode = False);
      sOverwriteFlag = dxBugIdConfig["bOverwriteDump"] and "/o" or "";
      oCdbWrapper.fasSendCommandAndReadOutput( \
          ".dump %s /ma \"%s\"; $$ Save dump to file" % (sOverwriteFlag, sValidDumpFileName));
      if not oCdbWrapper.bCdbRunning: return;
