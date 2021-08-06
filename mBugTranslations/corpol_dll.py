from .cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# AVE@Arbitrary -> Ignored
aoBugTranslations.append(cBugTranslation(
  # corpol.dll can test if DEP is enabled by storing a RET instruction in RW memory and calling it. This causes an
  # access violation if DEP is enabled, which is caught and handled. Therefore this exception should be ignored:
  srzOriginalBugTypeId = r"AVE@Arbitrary",
  azs0rbAppliesOnlyToTopStackFrame = [
    rb"\(unknown\)", # The location where the RET instruction is stored is not inside a module and has no symbol.
    rb"corpol\.dll!IsNxON",
  ],
  s0zTranslatedBugTypeId = None, # This is not a bug; allow the application to continue running.
  s0zTranslatedBugDescription = None,
  s0zTranslatedSecurityImpact = None,
));
