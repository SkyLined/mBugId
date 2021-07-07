import re;
from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # hide irrelevant frames
  cBugTranslation(
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"combase\.dll!SendReport",
      rb"combase\.dll!RoOriginateError",
      rb"combase\.dll!RoFailFastWithErrorContextInternal2",
      rb".*!RoFailFastWithErrorContext", # This function is actually in the binary that contains the code that triggered it.
    ],
  ),
];
