import re;
from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Everything reported through a verifier stop should get the verifier calls removed, as these are not relevant to
  # the bug; they are only the messenger.
  cBugTranslation(
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"verifier\.dll!.*",
    ],
  ),
];
