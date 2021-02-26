import mWindowsSDK;

gdtsTypeId_and_s0SecurityImpact_by_sDefineName = {
  "STATUS_WX86_SINGLE_STEP":               ("SingleStep",             None),
  "STATUS_WX86_BREAKPOINT":                ("Breakpoint",             None),
  "WRT_ORIGINATE_ERROR_EXCEPTION":         ("WRTOriginate",           None),
  "WRT_TRANSFORM_ERROR_EXCEPTION":         ("WRTTransform",           None),
  "STATUS_GUARD_PAGE_VIOLATION":           ("GuardPage",              "May be a security issue, but probably not exploitable"),
  "STATUS_DATATYPE_MISALIGNMENT":          ("DataMisalign",           "May be a security issue"),
  "STATUS_BREAKPOINT":                     ("Breakpoint",             None),
  "STATUS_SINGLE_STEP":                    ("SingleStep",             None),
  "ERROR_NOT_ENOUGH_MEMORY":               ("OOM",                    None),
  "ERROR_OUTOFMEMORY":                     ("OOM",                    None),
  "STATUS_NOT_IMPLEMENTED":                ("PureCall",               "May be a security issue"),
  "STATUS_ACCESS_VIOLATION":               ("AV",                     "May be a security issue"),
  "STATUS_INVALID_HANDLE":                 ("InvalidHandle",          None),
  "STATUS_NO_MEMORY":                      ("OOM",                    None),
  "STATUS_ILLEGAL_INSTRUCTION":            ("IllegalInstruction",     "May be a security issue, as it could indicate the instruction pointer was corrupted"),
  "STATUS_ARRAY_BOUNDS_EXCEEDED":          ("ArrayBounds",            "May be a security issue, but probably not exploitable"),
  "STATUS_FLOAT_DENORMAL_OPERAND":         ("FloatDenormalOperand",   None),
  "STATUS_FLOAT_DIVIDE_BY_ZERO":           ("FloatDivideByZero",      None),
  "STATUS_FLOAT_INEXACT_RESULT":           ("FloatInexactResult",     None),
  "STATUS_FLOAT_INVALID_OPERATION":        ("FloatInvalidOperation",  None),
  "STATUS_FLOAT_OVERFLOW":                 ("FloatOverflow",          None),
  "STATUS_FLOAT_STACK_CHECK":              ("FloatStackCheck",        None),
  "STATUS_FLOAT_UNDERFLOW":                ("FloatUnderflow",         None),
  "STATUS_INTEGER_DIVIDE_BY_ZERO":         ("IntegerDivideByZero",    None),
  "STATUS_INTEGER_OVERFLOW":               ("IntegerOverflow",        None),
  "STATUS_PRIVILEGED_INSTRUCTION":         ("PrivilegedInstruction",  "May be a security issue, as it could indicate the instruction pointer was corrupted"),
  "STATUS_STACK_OVERFLOW":                 ("StackExhaustion",        None),
  "STATUS_FAILFAST_OOM_EXCEPTION":         ("OOM",                    None),
  "STATUS_STOWED_EXCEPTION":               ("WRTLanguage",            None),
  "STATUS_STACK_BUFFER_OVERRUN":           ("FailFast2",              "Potentially exploitable security issue"),
  "STATUS_FATAL_USER_CALLBACK_EXCEPTION":  ("Verifier",               "May be a security issue"),
  "STATUS_ASSERTION_FAILURE":              ("Assert",                 None),
  "STATUS_FAIL_FAST_EXCEPTION":            ("FailFast",               "May be a security issue"),
  "CPP_EXCEPTION_CODE":                    ("C++",                    None),
};

class cErrorDetails(object):
  @staticmethod
  def fo0GetForCode(uErrorCode):
    # Best effort; we do not know what they type is, so we may get it wrong.
    
    # It may be an exception code:
    s0DefineName = mWindowsSDK.fs0GetExceptionDefineName(uErrorCode);
    if s0DefineName is not None:
      return cErrorDetails(uErrorCode, s0DefineName, "Exception 0x%08X (%s)" % (uErrorCode, s0DefineName));
    # It may be a Win32 Error Code:
    s0DefineName = mWindowsSDK.fs0GetWin32ErrorCodeDefineName(uErrorCode);
    if s0DefineName is not None:
      return cErrorDetails(uErrorCode, s0DefineName, "Win32 Error Code 0x%X (%s)" % (uErrorCode, s0DefineName));
    # It may be an NTSTATUS code:
    s0DefineName = mWindowsSDK.fs0GetNTStatusDefineName(uErrorCode);
    if s0DefineName is not None:
      return cErrorDetails(uErrorCode, s0DefineName, "NTSTATUS 0x%08X (%s)" % (uErrorCode, s0DefineName));
    # If it starts with `8007`, it may be a Win32 Error Code converted to an HRESULT.
    if uErrorCode & 0xFFFF0000 == 0x80070000:
      # The Win32 Error Code is stored in the lower 16 bits:
      s0DefineName = mWindowsSDK.fs0GetWin32ErrorCodeDefineName(uErrorCode & 0xFFFF);
      if s0DefineName is not None:
        return cErrorDetails(uErrorCode, s0DefineName, "HRESULT from Win32 Error Code 0x%X (%s)" % (uErrorCode & 0xFFFF, s0DefineName));
    # It may be an HResult:
    s0DefineName = mWindowsSDK.fs0GetHResultDefineName(uErrorCode);
    if s0DefineName is not None:
      return cErrorDetails(uErrorCode, s0DefineName, "HRESULT 0x%08X (%s)" % (uErrorCode, s0DefineName));
    # We have no idea what this error code means:
    return None;
    
  def __init__(oSelf, uCode, sDefineName, sDescription):
    global gdtsTypeId_and_s0SecurityImpact_by_sDefinedName;
    
    oSelf.uCode = uCode;
    oSelf.sDefineName = sDefineName;
    oSelf.sDescription = sDescription;
    if sDefineName in gdtsTypeId_and_s0SecurityImpact_by_sDefineName:
      (oSelf.sTypeId, oSelf.s0SecurityImpact) = gdtsTypeId_and_s0SecurityImpact_by_sDefineName[sDefineName];
    else:
      oSelf.sTypeId = sDefineName;
      oSelf.s0SecurityImpact = None; # Presumed
