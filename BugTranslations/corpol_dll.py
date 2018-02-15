from .cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# AVE@Arbitrary -> Ignored
aoBugTranslations.append(cBugTranslation(
  # corpol.dll can test if DEP is enabled by storing a RET instruction in RW memory and calling it. This causes an
  # access violation if DEP is enabled, which is caught and handled. Therefore this exception should be ignored:
  sOriginalBugTypeId = "AVE@Arbitrary",
  asOriginalTopStackFrameSymbols = [
    "(unknown)", # The location where the RET instruction is stored is not inside a module and has no symbol.
    "corpol.dll!IsNxON",
  ],
  sTranslatedBugTypeId = None, # This is not a bug; allow the application to continue running.
  sTranslatedBugDescription = None,
  sTranslatedSecurityImpact = None,
));
