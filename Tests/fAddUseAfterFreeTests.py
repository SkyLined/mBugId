from mTestLevels import NORMAL, FULL;

nExpectedTestTimeOnX64 = 2;

def fAddUseAfterFreeTests(dxTests):
  dxTests["UseAfterFree"] = {
    # Page heap may keep freed pages as reserved memory rather than allocated as NO_ACCESS.
    # At the moment this means we may not get a very useful BugId.
    "Read": [
      (NORMAL, [ 1,  0], [r"(AVR:Reserved\[4n\]@4n|RAF\[1\]@0) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],             nExpectedTestTimeOnX64),
      (FULL,   [ 1,  1], [r"(AVR:Reserved\[4n\]@4n\+1|OOBRAF\[1\]\+0) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],      nExpectedTestTimeOnX64),
      (FULL,   [ 3,  2], [r"(AVR:Reserved\[4n\]@4n\+2|RAF\[3\]@2) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],          nExpectedTestTimeOnX64),
      (FULL,   [ 5,  4], [r"(AVR:Reserved\[4n\]@4n|RAF\[4n\+1\]@4n) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],        nExpectedTestTimeOnX64),
      (FULL,   [ 3,  5], [r"(AVR:Reserved\[4n\]@4n\+1|OOBRAF\[3\]\+2) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],      nExpectedTestTimeOnX64),
      (FULL,   [ 5,  9], [r"(AVR:Reserved\[4n\]@1|OOBRAF\[4n\+1\]\+4n) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],     nExpectedTestTimeOnX64),
      (FULL,   [ 1, -1], [r"(AVR:Reserved\[4n\]@4n\+3|OOBRAF\[1\]\-1) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],      nExpectedTestTimeOnX64),
      (FULL,   [ 1, -3], [r"(AVR:Reserved\[4n\]@4n\+1|OOBRAF\[1\]\-3) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],      nExpectedTestTimeOnX64),
      (FULL,   [ 1, -5], [r"(AVR:Reserved\[4n\]@4n\+3|OOBRAF\[1\]\-4n\-1) (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],  nExpectedTestTimeOnX64),
    ],
    "Write": [
      (FULL,   [ 2,  1], [r"(AVW:Reserved\[4n\]@4n\+1|WAF\[2\]@1) (975\.540|113\.80a) @ <binary>!fWriteByte"],          nExpectedTestTimeOnX64),
      (FULL,   [ 4,  3], [r"(AVW:Reserved\[4n\]@4n\+3|WAF\[4n\]@3) (975\.540|113\.80a) @ <binary>!fWriteByte"],         nExpectedTestTimeOnX64),
      (FULL,   [ 6,  5], [r"(AVW:Reserved\[4n\]@4n\+1|WAF\[4n\+2\]@4n\+1) (975\.540|113\.80a) @ <binary>!fWriteByte"],  nExpectedTestTimeOnX64),
      (FULL,   [ 2,  3], [r"(AVW:Reserved\[4n\]@4n\+3|OOBWAF\[2\]\+1) (975\.540|113\.80a) @ <binary>!fWriteByte"],      nExpectedTestTimeOnX64),
      (FULL,   [ 4,  7], [r"(AVW:Reserved\[4n\]@4n\+3|OOBWAF\[4n\]\+3) (975\.540|113\.80a) @ <binary>!fWriteByte"],     nExpectedTestTimeOnX64),
      (FULL,   [ 6, 11], [r"(AVW:Reserved\[4n\]@3|OOBWAF\[4n\+2\]\+4n\+1) (975\.540|113\.80a) @ <binary>!fWriteByte"],  nExpectedTestTimeOnX64),
      (FULL,   [ 1, -2], [r"(AVW:Reserved\[4n\]@4n\+2|OOBWAF\[1\]\-2) (975\.540|113\.80a) @ <binary>!fWriteByte"],      nExpectedTestTimeOnX64),
      (FULL,   [ 1, -4], [r"(AVW:Reserved\[4n\]@4n|OOBWAF\[1\]\-4n) (975\.540|113\.80a) @ <binary>!fWriteByte"],        nExpectedTestTimeOnX64),
    ],
    "Call": [
      (FULL,   [ 8,  0], [r"(AVE:Reserved\[4n\]@4n|EAF\[4n\]@0) (b2d\.540|681\.80a) @ <binary>!fCall"],                 nExpectedTestTimeOnX64),
      (FULL,   [ 8,  8], [r"(AVE:Reserved\[4n\]@0|OOBEAF\[4n\]\+0) (b2d\.540|681\.80a) @ <binary>!fCall"],              nExpectedTestTimeOnX64),
    ],
    "Jump": [
      (FULL,   [ 8,  0], [r"(AVE:Reserved\[4n\]@4n|EAF\[4n\]@0) (414\.540|fb0\.80a) @ <binary>!fJump"],                 nExpectedTestTimeOnX64),
      (FULL,   [ 8,  8], [r"(AVE:Reserved\[4n\]@0|OOBEAF\[4n\]\+0) (414\.540|fb0\.80a) @ <binary>!fJump"],              nExpectedTestTimeOnX64),
    ],
  };
