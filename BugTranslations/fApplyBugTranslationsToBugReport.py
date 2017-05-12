from ASan import aoBugTranslations as aoBugTranslations_ASan;
from CFG import aoBugTranslations as aoBugTranslations_CFG;
from Chrome import aoBugTranslations as aoBugTranslations_Chrome;
from combase import aoBugTranslations as aoBugTranslations_combase;
from Corpol import aoBugTranslations as aoBugTranslations_Corpol;
from Cpp import aoBugTranslations as aoBugTranslations_Cpp;
from Edge import aoBugTranslations as aoBugTranslations_Edge;
from Firefox import aoBugTranslations as aoBugTranslations_Firefox;
from kernelbase import aoBugTranslations as aoBugTranslations_kernelbase;
from MSIE import aoBugTranslations as aoBugTranslations_MSIE;
from ntdll import aoBugTranslations as aoBugTranslations_ntdll;
from RTC import aoBugTranslations as aoBugTranslations_RTC;
from verifier import aoBugTranslations as aoBugTranslations_verifier;

aoBugTranslations = (
  aoBugTranslations_ASan
  + aoBugTranslations_CFG
  + aoBugTranslations_Chrome
  + aoBugTranslations_combase
  + aoBugTranslations_Corpol
  + aoBugTranslations_Cpp
  + aoBugTranslations_Edge
  + aoBugTranslations_Firefox
  + aoBugTranslations_kernelbase
  + aoBugTranslations_MSIE
  + aoBugTranslations_ntdll
  + aoBugTranslations_RTC
  + aoBugTranslations_verifier
);

def fApplyBugTranslationsToBugReport(oBugReport):
  # Apply transformations until there is none that applies.
  while oBugReport.sBugTypeId is not None:
    for oBugTranslation in aoBugTranslations:
      if oBugTranslation.fbApplyToBugReport(oBugReport):
        # This bug translation was applied: restart.
        break;
    else:
      # No translations apply: done.
      return;
