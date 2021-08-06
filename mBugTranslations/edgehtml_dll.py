from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # OOM -> hide irelevant frames
  cBugTranslation(
    srzOriginalBugTypeId = r"OOM",
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"edgehtml\.dll!Streams::Chunk<.+>::InternalAlloc",
    ],
  ),
];
