from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # OOM -> hide irelevant frames
  cBugTranslation(
    srzOriginalBugTypeId = r"OOM",
    asrbAdditionalIrrelevantStackFrameSymbols = [
      rb"edgehtml\.dll!Streams::Chunk<.+>::InternalAlloc",
    ],
  ),
];
