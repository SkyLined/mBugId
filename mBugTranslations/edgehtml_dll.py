from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # OOM -> hide irrelevant frames
  cBugTranslation(
    srzOriginalBugTypeId = r"OOM",
    azs0rbAdditionalIrrelevantStackFrameSymbols = [
      rb"edgehtml\.dll!Streams::Chunk<.+>::InternalAlloc",
    ],
  ),
];
