import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # WRTOriginate => hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = re.compile(r"^WRTOriginate\[.*\]$"),
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "combase.dll!SendReport",
      ], [
        "combase.dll!RoOriginateError",
      ],
    ],
  ),
  # Stowed[...] => hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = re.compile(r"^Stowed\[.+\]$"),
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "combase.dll!RoFailFastWithErrorContextInternal2",
      ], [
        "*!RoFailFastWithErrorContext", # This function is actually in the binary that contains the code that triggered it.
      ],
    ],
  ),
];
