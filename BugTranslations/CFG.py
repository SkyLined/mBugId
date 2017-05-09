from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# AVR@Reserved -> AVR@CFG
aoBugTranslations.append(cBugTranslation(
  sOriginalBugTypeId = "AVR@Reserved",
  aasOriginalTopStackFrameSymbols = [
    [
      "ntdll.dll!LdrpDispatchUserCallTarget",
    ], [
      "ntdll.dll!LdrpValidateUserCallTargetBitMapCheck",
    ], [
      "ntdll.dll!LdrpValidateUserCallTarget",
    ],
  ],
  sTranslatedBugTypeId = "AVR@CFG",
  sTranslatedBugDescription = "The process attempted to call a function using an invalid function pointer, " \
      "which caused an acces violation exception in Control Flow Guard. This is often caused by a NULL pointer.",
  sTranslatedSecurityImpact = "Unlikely to be an exploitable security issue, unless you can control the invalid function pointer",
));
