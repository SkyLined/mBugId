from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # OOM -> hide irelevant frames
  cBugTranslation(
    sOriginalBugTypeId = "OOM",
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "edgehtml.dll!Streams::Chunk<...>::InternalAlloc",
      ],
    ],
  ),
];
