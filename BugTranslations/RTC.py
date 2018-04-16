from .cBugTranslation import cBugTranslation;

aoBugTranslations = [];
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "Breakpoint",
  asOriginalTopStackFrameSymbols = [
    "*!failwithmessage",
    "*!_RTC_StackFailure",
  ],
  aasAdditionalIrrelevantStackFrameSymbols = [
    [
      "*!_RTC_CheckStackVars",
    ], [
      "*!_RTC_CheckStackVars2",
    ],
  ],
  sTranslatedBugTypeId = "OOBW@Stack",
  sTranslatedBugDescription = "The Windows Run-Time detected that a stack variable was modified, which suggests an out-of-bounds write on the stack.",
  sTranslatedSecurityImpact = "Potentially exploitable security issue",
));
