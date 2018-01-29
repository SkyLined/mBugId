import re;
from cBugTranslation import cBugTranslation;

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
  # OOM, HeapCorrupt, DoubleFree, MisalignedFree, OOBW -> hide irrelevant frames
  cBugTranslation(
    sOriginalBugTypeId = re.compile(r"^(OOM|HeapCorrupt|DoubleFree\[.*|MisalignedFree\[.*|OOBW\[.*)$"),
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "kernelbase.dll!LocalFree",
      ],
    ],
  ),
];
