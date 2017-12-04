import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # All these are never relevant to the bug
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "verifier.dll!AVrfDebugPageHeapAllocate",
      ], [
        "verifier.dll!AVrfDebugPageHeapFree",
      ], [
        "verifier.dll!AVrfpDphCheckNormalHeapBlock",
      ], [
        "verifier.dll!AVrfpDphCheckPageHeapBlock",
      ], [
        "verifier.dll!AVrfpDphCompareNodeForTable",
      ], [
        "verifier.dll!AVrfpDphFindBusyMemory",
      ], [
        "verifier.dll!AVrfpDphFindBusyMemoryAndRemoveFromBusyList",
      ], [
        "verifier.dll!AVrfpDphFindBusyMemoryNoCheck",
      ], [
        "verifier.dll!AVrfpDphNormalHeapFree",
      ], [
        "verifier.dll!AVrfpDphPageHeapFree",
      ], [
        "verifier.dll!AVrfpDphPlaceOnBusyList",
      ], [
        "verifier.dll!AVrfpDphRaiseException",
      ], [
        "verifier.dll!AVrfpDphReportCorruptedBlock",
      ], [
        "verifier.dll!VerifierBreakin",
      ], [
        "verifier.dll!VerifierCaptureContextAndReportStop",
      ], [
        "verifier.dll!VerifierStopMessage",
      ],
    ],
  ),
];
