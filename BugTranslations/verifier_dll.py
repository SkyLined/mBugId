import re;
from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Everything reported through a verifier stop should get the verifier calls removed, as these are not relevant to
  # the bug; they are only the messenger.
  cBugTranslation(
    sOriginalBugTypeId = re.compile(r"^(%s)(\[\d.*|\[\?\]|@\w+)?$" % "|".join([
      "DoubleFree",
      "HeapCorrupt",
      "MisalignedFree",
      "OOM",
      "OOBW",
      "WAF",
      "BOF",
      "WrongHeap",
    ])),
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
