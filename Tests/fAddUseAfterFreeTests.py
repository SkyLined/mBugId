from mTestLevels import NORMAL, FULL, FULL_x86, FULL_x64;

nExpectedTestTimeOnX64 = 2;

def fAddUseAfterFreeTests(dxTests):
  srMainIdAndLocation = r"5b3 @ <binary>!wmain";
  srCallIdAndLocation = r"3e6\.5b3 @ <binary>!fCall";
  srJumpIdAndLocation = r"e8c\.5b3 @ <binary>!fJump";
  dxTests["HeapUseAfterFree"] = {
    # Page heap may keep freed pages as reserved memory rather than allocated as NO_ACCESS.
    # At the moment this means we may not get a very useful BugId.
    "Read": [
      (NORMAL,    [ 1,  0], [r"(AVR:Reserved\[4n\]@4n|RAF\[1\]@0) " + srMainIdAndLocation],             nExpectedTestTimeOnX64),
      (FULL,      [ 1,  1], [r"(AVR:Reserved\[4n\]@4n\+1|OOBRAF\[1\]\+0) " + srMainIdAndLocation],      nExpectedTestTimeOnX64),
      (FULL,      [ 3,  2], [r"(AVR:Reserved\[4n\]@4n\+2|RAF\[3\]@2) " + srMainIdAndLocation],          nExpectedTestTimeOnX64),
      (FULL,      [ 5,  4], [r"(AVR:Reserved\[4n\]@4n|RAF\[4n\+1\]@4n) " + srMainIdAndLocation],        nExpectedTestTimeOnX64),
      (FULL,      [ 3,  5], [r"(AVR:Reserved\[4n\]@4n\+1|OOBRAF\[3\]\+2) " + srMainIdAndLocation],      nExpectedTestTimeOnX64),
      # This is worth investigating, as it looks wrong on x86 to me.
      # Unfortunately, I do not current have the time.
      (FULL_x86,  [ 5,  9], [r"(AVR:Reserved\[4n\]@1|OOBRAF\[4n\+1\]\+4n) " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL_x64,  [ 5,  9], [r"(AVR:Reserved\[4n\]@4n\+1|OOBRAF\[4n\+1\]\+4n) " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,      [ 1, -1], [r"(AVR:Reserved\[4n\]@4n\+3|OOBRAF\[1\]\-1) " + srMainIdAndLocation],      nExpectedTestTimeOnX64),
      (FULL,      [ 1, -3], [r"(AVR:Reserved\[4n\]@4n\+1|OOBRAF\[1\]\-3) " + srMainIdAndLocation],      nExpectedTestTimeOnX64),
      (FULL,      [ 1, -5], [r"(AVR:Reserved\[4n\]@4n\+3|OOBRAF\[1\]\-4n\-1) " + srMainIdAndLocation],  nExpectedTestTimeOnX64),
    ],
    "Write": [
      (FULL,      [ 2,  1], [r"(AVW:Reserved\[4n\]@4n\+1|WAF\[2\]@1) " + srMainIdAndLocation],          nExpectedTestTimeOnX64),
      (FULL,      [ 4,  3], [r"(AVW:Reserved\[4n\]@4n\+3|WAF\[4n\]@3) " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,      [ 6,  5], [r"(AVW:Reserved\[4n\]@4n\+1|WAF\[4n\+2\]@4n\+1) " + srMainIdAndLocation],  nExpectedTestTimeOnX64),
      (FULL,      [ 2,  3], [r"(AVW:Reserved\[4n\]@4n\+3|OOBWAF\[2\]\+1) " + srMainIdAndLocation],      nExpectedTestTimeOnX64),
      (FULL,      [ 4,  7], [r"(AVW:Reserved\[4n\]@4n\+3|OOBWAF\[4n\]\+3) " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      # This is worth investigating, as it looks wrong on x86 to me.
      # Unfortunately, I do not current have the time.
      (FULL_x86,  [ 6, 11], [r"(AVW:Reserved\[4n\]@3|OOBWAF\[4n\+2\]\+4n\+1) " + srMainIdAndLocation],  nExpectedTestTimeOnX64),
      (FULL_x64,  [ 6, 11], [r"(AVW:Reserved\[4n\]@4n\+3|OOBWAF\[4n\+2\]\+4n\+1) " + srMainIdAndLocation],  nExpectedTestTimeOnX64),
      (FULL,      [ 1, -2], [r"(AVW:Reserved\[4n\]@4n\+2|OOBWAF\[1\]\-2) " + srMainIdAndLocation],      nExpectedTestTimeOnX64),
      (FULL,      [ 1, -4], [r"(AVW:Reserved\[4n\]@4n|OOBWAF\[1\]\-4n) " + srMainIdAndLocation],        nExpectedTestTimeOnX64),
    ],
    "Call": [
      (FULL,      [ 8,  0], [r"(AVE:Reserved\[4n\]@4n|EAF\[4n\]@0) " + srCallIdAndLocation],                 nExpectedTestTimeOnX64),
      # This is worth investigating, as it looks wrong on x86 to me.
      # Unfortunately, I do not current have the time.
      (FULL_x86,  [ 8,  8], [r"(AVE:Reserved\[4n\]@0|OOBEAF\[4n\]\+0) " + srCallIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64,  [ 8,  8], [r"(AVE:Reserved\[4n\]@4n|OOBEAF\[4n\]\+0) " + srCallIdAndLocation],              nExpectedTestTimeOnX64),
    ],
    "Jump": [
      (FULL,      [ 8,  0], [r"(AVE:Reserved\[4n\]@4n|EAF\[4n\]@0) " + srJumpIdAndLocation],                 nExpectedTestTimeOnX64),
      # This is worth investigating, as it looks wrong on x86 to me.
      # Unfortunately, I do not current have the time.
      (FULL_x86,  [ 8,  8], [r"(AVE:Reserved\[4n\]@0|OOBEAF\[4n\]\+0) " + srJumpIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64,  [ 8,  8], [r"(AVE:Reserved\[4n\]@4n|OOBEAF\[4n\]\+0) " + srJumpIdAndLocation],              nExpectedTestTimeOnX64),
    ],
  };
