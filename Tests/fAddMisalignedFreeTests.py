from mTestLevels import NORMAL, FULL;

nExpectedTestTimeOnX64 = 2;

def fAddMisalignedFreeTests(dxTests):
  srIdAndLocation = r"3b0\.5b3 @ <binary>!fFreeAllocatedHeapMemory";
  dxTests["HeapMisalignedFree"] = [
    (NORMAL,  [ 1,  1], [r"MisalignedFree\[1\]\+0 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 1,  2], [r"MisalignedFree\[1\]\+1 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 2,  4], [r"MisalignedFree\[2\]\+2 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 3,  6], [r"MisalignedFree\[3\]\+3 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 4,  8], [r"MisalignedFree\[4n\]\+4n " + srIdAndLocation],         nExpectedTestTimeOnX64),
    (FULL,    [ 5, 10], [r"MisalignedFree\[4n\+1\]\+4n\+1 " + srIdAndLocation],   nExpectedTestTimeOnX64),
    (FULL,    [ 2,  1], [r"MisalignedFree\[2\]@1 " + srIdAndLocation],            nExpectedTestTimeOnX64),
    (FULL,    [ 3,  2], [r"MisalignedFree\[3\]@2 " + srIdAndLocation],            nExpectedTestTimeOnX64),
    (FULL,    [ 4,  3], [r"MisalignedFree\[4n\]@3 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 5,  4], [r"MisalignedFree\[4n\+1\]@4n " + srIdAndLocation],       nExpectedTestTimeOnX64),
    (FULL,    [ 1, -1], [r"MisalignedFree\[1\]\-1 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 1, -2], [r"MisalignedFree\[1\]\-2 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 1, -3], [r"MisalignedFree\[1\]\-3 " + srIdAndLocation],           nExpectedTestTimeOnX64),
    (FULL,    [ 1, -4], [r"MisalignedFree\[1\]\-4n " + srIdAndLocation],          nExpectedTestTimeOnX64),
    (FULL,    [ 1, -5], [r"MisalignedFree\[1\]\-4n\-1 " + srIdAndLocation],       nExpectedTestTimeOnX64),
  ];
