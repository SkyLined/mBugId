import re;
from cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Assert -> OOM
  cBugTranslation(
    sOriginalBugTypeId = re.compile("^Assert(:HRESULT)?$"),
    asOriginalTopStackFrameSymbols = [
      "*!CIsoMalloc::_InitializeEntry",
    ],
    aasAdditionalIrrelevantStackFrameSymbols = [
      [
        "*!CIsoScope::_AllocArtifact",
      ], [
        "*!CIsoSList::AllocArtifact",
      ], [
        "*!CIsoScope::_AllocMessageBuffer",
      ], [
        "*!CIsoScope::AllocMessageBuffer",
      ], [
        "*!IsoAllocMessageBuffer",
      ],
    ],
    sTranslatedBugTypeId = "OOM",
    sTranslatedBugDescription = "The application triggered a fail fast application exit to indicate it was unable to allocate enough memory.",
    sTranslatedSecurityImpact = "Unlikely to be exploitable, unless you can find a way to avoid this breakpoint.",
  ),
];
