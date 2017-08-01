import json, re;
from cStack import cStack;
from dxConfig import dxConfig;

def cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION(oBugReport, oProcess, oException):
  # Seee documentation of RoOriginateError at https://msdn.microsoft.com/en-us/library/br224651(v=vs.85).aspx
  # Parameter[0] = HRESULT error;
  # Parameter[1] = length of HSTRING message;
  # Parameter[2] = pointer to HSTRING message;
  assert len(oException.auParameters) == 3, \
      "Unexpected number of RoOriginateError exception parameters (%d vs 3)" % len(oException.auParameters);
  hResult = oException.auParameters[0];
  uMessageLength = oException.auParameters[1];
  uMessageAddress = oException.auParameters[2];
  # The message is '\0' terminated, so no need to use uMessageLength. We could assert if it's incorrect, but I don't see much use in that.
  if oException.bApplicationCannotHandleException:
    sMessage = oProcess.fsGetUnicodeString(
      uAddress = uMessageAddress,
      sComment = "Get WRT Originate Error message",
    );
    # Get the stowed exceptions and replace information in the bug report:
    oBugReport.sBugTypeId = "WRTOriginate[0x%X]" % hResult;
    oBugReport.sBugDescription = "A Windows Run-Time Originate error was thrown with error code %X and message %s." % \
        (hResult, json.dumps(sMessage));
    oBugReport.sSecurityImpact = "The security impact of this type of vulnerability is unknown";
  else:
    # This is not a bug, but we may want to show the message:
    oBugReport.sBugTypeId = None;
    if oProcess.oCdbWrapper.bGenerateReportHTML and dxConfig["bLogInReport"]:
      sMessage = oProcess.fsGetUnicodeString(
        uAddress = uMessageAddress,
        sComment = "Get WRT Originate Error message",
      );
      oProcess.oCdbWrapper.fLogMessageInReport(
        "LogException", 
        "The application threw a Windows Run-Time Originate Error with HRESULT 0x%08X:<br/>Message: %s</span>" % \
            (hResult, sMessage is None and "(no message)" or repr(sMessage))
      );
  return oBugReport;
