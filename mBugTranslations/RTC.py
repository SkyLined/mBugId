from .cBugTranslation import cBugTranslation;

aoBugTranslations = [];
aoBugTranslations.append(cBugTranslation(
  srzOriginalBugTypeId = r"Breakpoint",
  azsrbAppliesOnlyToTopStackFrame = [
    rb".*!failwithmessage",
    rb".*!_RTC_StackFailure",
  ],
  asrbAdditionalIrrelevantStackFrameSymbols = [
    rb".*!_RTC_CheckStackVars\d*",
  ],
  s0zTranslatedBugTypeId = "OOBW:Stack",
  s0zTranslatedBugDescription = "The Windows Run-Time detected that a stack variable was modified, which suggests an out-of-bounds write on the stack.",
  s0zTranslatedSecurityImpact = "Potentially exploitable security issue",
));
