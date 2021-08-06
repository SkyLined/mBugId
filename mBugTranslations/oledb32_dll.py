from .cBugTranslation import cBugTranslation;

aoBugTranslations = [
  # Apparently this code will try to see if a string is NULL terminated by
  # scanning memory until it sees a NULL, regardless of the size of the buffer
  # This code is wrapped in an exception handler to detect when it is reading
  # memory out of bounds. This is of course a very bad idea, but it is how
  # things work in MS Office... sigh.
  cBugTranslation(
    srzOriginalBugTypeId = r"OOBR\[.*\].*",
    azs0rbAppliesOnlyToTopStackFrame = [
      rb"oledb32\.dll!SafeCheckWCharNullTermination",
    ],
    s0zTranslatedBugTypeId = None,
  ),
];