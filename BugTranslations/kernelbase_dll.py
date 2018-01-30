import re;
from cBugTranslation import cBugTranslation;
from rHeapRelatedBugIds import rHeapRelatedBugIds;

aoBugTranslations = [
  # * -> hide irrelevant frames
  cBugTranslation(
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!DebugBreak",
      ], [
        "kernelbase.dll!RaiseException",
      ], [
        "kernelbase.dll!RaiseFailFastException",
      ],
    ],
  ),
  # OOM -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!TerminateProcessOnMemoryExhaustion",
      ],
    ],
  ),
  # Heap related issues -> hide irrelevant heap management frames
  cBugTranslation(
    sOriginalBugTypeId = rHeapRelatedBugIds,
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!LocalFree",
      ],
    ],
  ),
];
