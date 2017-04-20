from cBugTranslation import cBugTranslation;

aoBugTranslations = [];
# AVR@Reserved -> AVR@CFG
for sCFGCallTargetValidationFunction in [
  "ntdll.dll!LdrpValidateUserCallTarget",
  "ntdll.dll!LdrpValidateUserCallTargetBitMapCheck",
  "ntdll.dll!LdrpDispatchUserCallTarget",
]:
  aoBugTranslations.append(cBugTranslation(
    sOriginalBugTypeId = "AVR@Reserved",
    asOriginalStackTopFrameAddresses = [
      sCFGCallTargetValidationFunction,
    ],
    sTranslatedBugTypeId = "AVR@CFG",
    sTranslatedBugDescription = "The process attempted to call a function using an invalid function pointer, " \
        "which caused an acces violation exception in Control Flow Guard. This is often caused by a NULL pointer.",
    sTranslatedSecurityImpact = "Unlikely to be an exploitable security issue, unless you can control the invalid function pointer",
  ));
