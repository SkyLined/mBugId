import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# Stowed[...] => hide irrelevant frames
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = re.compile(r"^Stowed\[.*\]$"),
  asOriginalTopStackFrameSymbols = [
    "combase.dll!RoFailFastWithErrorContextInternal2",
  ],
  aasAdditionalIrrelevantStackFrameSymbols = [
    [
      "combase.DLL!RoFailFastWithErrorContext",
    ],
  ],
));
