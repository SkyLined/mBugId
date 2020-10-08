from .ASan import aoBugTranslations as aoBugTranslations_ASan;
from .chakra_dll import aoBugTranslations as aoBugTranslations_chakra_dll;
from .Chrome import aoBugTranslations as aoBugTranslations_Chrome;
from .combase_dll import aoBugTranslations as aoBugTranslations_combase_dll;
from .conhost_exe import aoBugTranslations as aoBugTranslations_conhost_exe;
from .corpol_dll import aoBugTranslations as aoBugTranslations_corpol_dll;
from .Cpp import aoBugTranslations as aoBugTranslations_Cpp;
from .edgehtml_dll import aoBugTranslations as aoBugTranslations_edgehtml_dll;
from .edgecontent_dll import aoBugTranslations as aoBugTranslations_edgecontent_dll;
from .Firefox import aoBugTranslations as aoBugTranslations_Firefox;
from .iso import aoBugTranslations as aoBugTranslations_iso;
from .jscript9_dll import aoBugTranslations as aoBugTranslations_jscript9_dll;
from .kernelbase_dll import aoBugTranslations as aoBugTranslations_kernelbase_dll;
from .mshtml_dll import aoBugTranslations as aoBugTranslations_mshtml_dll;
from .ntdll_dll import aoBugTranslations as aoBugTranslations_ntdll_dll;
from .RTC import aoBugTranslations as aoBugTranslations_RTC;
from .SafeInt import aoBugTranslations as aoBugTranslations_SafeInt;
from .SlashGS import aoBugTranslations as aoBugTranslations_SlashGS;
from .ucrtbase_dll import aoBugTranslations as aoBugTranslations_ucrtbase_dll;
from .V8 import aoBugTranslations as aoBugTranslations_V8;
from .verifier_dll import aoBugTranslations as aoBugTranslations_verifier_dll;
from .wil import aoBugTranslations as aoBugTranslations_wil;

aoBugTranslations = [];
for aoBugTranslations_X in [
  aoBugTranslations_ASan,
  aoBugTranslations_chakra_dll,
  aoBugTranslations_Chrome,
  aoBugTranslations_combase_dll,
  aoBugTranslations_conhost_exe,
  aoBugTranslations_corpol_dll,
  aoBugTranslations_Cpp,
  aoBugTranslations_edgehtml_dll,
  aoBugTranslations_edgecontent_dll,
  aoBugTranslations_Firefox,
  aoBugTranslations_iso,
  aoBugTranslations_jscript9_dll,
  aoBugTranslations_kernelbase_dll,
  aoBugTranslations_mshtml_dll,
  aoBugTranslations_ntdll_dll,
  aoBugTranslations_RTC,
  aoBugTranslations_SafeInt,
  aoBugTranslations_SlashGS,
  aoBugTranslations_ucrtbase_dll,
  aoBugTranslations_V8,
  aoBugTranslations_verifier_dll,
  aoBugTranslations_wil,
]:
  aoBugTranslations += aoBugTranslations_X;


def fApplyBugTranslationsToBugReport(oBugReport):
  # Apply transformations until there is none that applies.
  uSanityCheckMaximumLoops = 0x1000; # This should never happen
  while oBugReport.sBugTypeId is not None:
    for oBugTranslation in aoBugTranslations:
      if oBugTranslation.fbApplyToBugReport(oBugReport):
        # This bug translation was applied: restart after checking that we're not in what appears to be an infinite
        # loop:
        uSanityCheckMaximumLoops -= 1;
        assert uSanityCheckMaximumLoops, \
            "A bug translation loop was detected that appears to involved %s being applied to %s @ %s" % \
            (str(oBugTranslation), oBugReport.sId, oBugReport.sBugLocation);
        break;
    else:
      # No translations apply: done.
      return;
