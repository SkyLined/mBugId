from .cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# OOBW@Stack (hide irrelevant frames only)
aoBugTranslations.append(cBugTranslation(
  srzOriginalBugTypeId = r"OOBW:Stack",
  azs0rbAppliesOnlyToTopStackFrame = [
    rb".*!__security_check_cookie",
  ],
));
