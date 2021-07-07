import json;
from .cStack import cStack;
from .dxConfig import dxConfig;

def cBugReport_foAnalyzeException_WRT_ORIGINATE_ERROR_EXCEPTION(oBugReport, oProcess, oThread, oException):
  # Seee documentation of RoOriginateError at https://msdn.microsoft.com/en-us/library/br224651(v=vs.85).aspx
  # Parameter[0] = HRESULT error;
  # Parameter[1] = length of HSTRING message;
  # Parameter[2] = pointer to HSTRING message;
  assert len(oException.auParameters) == 3, \
      "Unexpected number of RoOriginateError exception parameters (%d vs 3)" % len(oException.auParameters);
  hResult = oException.auParameters[0];
  # uMessageLength = oException.auParameters[1];
  uMessageAddress = oException.auParameters[2];
  # The message is '\0' terminated, so no need to use uMessageLength.
  # We could assert if it's incorrect, but I don't see much use in that other than to prevent the target from
  # crashing us.
  if oException.bApplicationCannotHandleException:
    s0Message = oProcess.fs0ReadNullTerminatedStringForAddress(
      uAddress = uMessageAddress,
      bUnicode = True,
    );
    # Get the stowed exceptions and replace information in the bug report:
    oBugReport.s0BugTypeId = "WRTOriginate[0x%X]" % hResult;
    oBugReport.s0BugDescription = "A Windows Run-Time Originate error was thrown with error code %X and message %s." % \
        (hResult, json.dumps(s0Message) if s0Message else "<unknown>");
    oBugReport.s0SecurityImpact = "Unknown";
  else:
    # This is not a bug:
    oBugReport.s0BugTypeId = None;
    oBugReport.s0BugDescription = None;
  return oBugReport;
