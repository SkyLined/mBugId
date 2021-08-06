import re;
from .cBugTranslation import cBugTranslation;

def fDisableDetectionOfAccessViolations(oCdbWrapper, oBugReport):
  oCdbWrapper.fbFireCallbacks("ASan detected");
  oCdbWrapper.fasbExecuteCdbCommand(
    sbCommand = b"sxd av",
    sb0Comment = b"Disable handling of exceptions because ASan throws too many",
  );

aoBugTranslations = [
  # AVs during initialization --> expected, not a bug.
  cBugTranslation(
    srzOriginalBugTypeId = r"AVW:Reserved\[(0x)?[\dA-F]+n?\]@\d+",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!__asan::FastPoisonShadow",
    ],
    s0zTranslatedBugTypeId = None,
    f0Callback = fDisableDetectionOfAccessViolations
  ),
  # IllegalInstruction --> ASan
  cBugTranslation(
    srzOriginalBugTypeId = r"IllegalInstruction",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb".*!__sanitizer::Trap",
    ],
    s0zTranslatedBugTypeId = "ASan",
    # This is a backup in case cAsanErrorDetector does not detect and handle the ASan debug output we normally expect.
    s0zTranslatedBugDescription = "ASan triggered an illegal instruction to indicate it detected an issue which cBugId does not recognize.",
    s0zTranslatedSecurityImpact = "The security implications of this issue are unknown",
  ),
  # ASan --> (hide irrelevant frames only)
  cBugTranslation(
    srzOriginalBugTypeId = "ASan",
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb".*!agent::asan::\w+.*",
      rb".*!_*asan_\w+.*",
      rb".*!__asan::\w+.*",
      rb".*!__sanitizer::\w+.*",
      rb".*!uprv_realloc_60",
    ],
  ),
];