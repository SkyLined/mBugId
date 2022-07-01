# test selection flags
uRunForQuickTests  =      1;
uRunForNormalTests =      2;
uRunForFullTests   =      4;
uRunFor_x86        =   0x10;
uRunFor_x64        =   0x20;
uRunForAnyISA      =  uRunFor_x86 | uRunFor_x64;
# test selection keywords
QUICK       = uRunForQuickTests | uRunForNormalTests | uRunForFullTests | uRunForAnyISA;
NORMAL      = uRunForNormalTests | uRunForFullTests | uRunForAnyISA;
FULL        = uRunForFullTests | uRunForAnyISA;
NOT_FULL    = uRunForNormalTests | uRunForAnyISA;
x86         = uRunForNormalTests | uRunForFullTests | uRunFor_x86;
x64         = uRunForNormalTests | uRunForFullTests | uRunFor_x64;
FULL_x86    = uRunForFullTests | uRunFor_x86;
FULL_x64    = uRunForFullTests | uRunFor_x64;
