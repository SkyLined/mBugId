import re;
from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # IllegalInstruction --> ASan
  cBugTranslation(
    sOriginalBugTypeId = "IllegalInstruction",
    asOriginalTopStackFrameSymbols = [
      "*!__sanitizer::Trap",
    ],
    sTranslatedBugTypeId = "ASan",
    # This is a backup in case cAsanErrorDetector does not detect and handle the ASan debug output we normally expect.
    sTranslatedBugDescription = "ASan triggered an illegal instruction to indicate it detected an issue which cBugId does not recognize.",
    sTranslatedSecurityImpact = "The security implications of this issue are unknown",
  ),
  # Asan (hide irrelevant frames only)
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        re.compile(r".*!agent::asan::\w+.*"),
      ], [
        re.compile(r".*!asan_\w+.*"),
      ], [
        re.compile(r".*!__asan_\w+.*"),
      ], [
        re.compile(r".*!__asan::\w+.*"),
      ], [
        re.compile(r".*!__sanitizer::\w+.*"),
      ], [
        ".*!uprv_realloc_60",
      ],
    ],
  ),
];