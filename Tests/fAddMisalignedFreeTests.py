from mTestLevels import NORMAL, FULL;

def fAddMisalignedFreeTests(dxTests):
  dxTests["MisalignedFree"] = [
    (NORMAL,  [ 1,  1], [r"MisalignedFree\[1\]\+0 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 1,  2], [r"MisalignedFree\[1\]\+1 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 2,  4], [r"MisalignedFree\[2\]\+2 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 3,  6], [r"MisalignedFree\[3\]\+3 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 4,  8], [r"MisalignedFree\[4n\]\+4n (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 5, 10], [r"MisalignedFree\[4n\+1\]\+4n\+1 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 2,  1], [r"MisalignedFree\[2\]@1 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 3,  2], [r"MisalignedFree\[3\]@2 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 4,  3], [r"MisalignedFree\[4n\]@3 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 5,  4], [r"MisalignedFree\[4n\+1\]@4n (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 1, -1], [r"MisalignedFree\[1\]\-1 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 1, -2], [r"MisalignedFree\[1\]\-2 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 1, -3], [r"MisalignedFree\[1\]\-3 (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 1, -4], [r"MisalignedFree\[1\]\-4n (540|80a) @ <binary>!wmain"]),
    (FULL,    [ 1, -5], [r"MisalignedFree\[1\]\-4n\-1 (540|80a) @ <binary>!wmain"]),
  ];
