from mTestLevels import NORMAL, FULL;

def fAddOutOfBoundsTests(dxTests, uLargeHeapBlockSize):
  dxTests["OutOfBounds"] = {
    "Heap": {
      "Write": [
        # Small out-of-bounds writes that do not go outside of the memory page and therefore do not cause access violations.
        # These are detected by Page Heap / Application Verifier when the memory is freed.
        # This means it is not reported in the `fWriteByte` function that does the writing, but in wmain that does the freeing.
        (NORMAL,  [ 1, -1, 1], [r"OOBW\[1\]\{\-1~1\} (540|80a) @ <binary>!wmain"]),
        (FULL,    [ 2, -2, 2], [r"OOBW\[2\]\{\-2~2\} (540|80a) @ <binary>!wmain"]),
        (FULL,    [ 3, -3, 3], [r"OOBW\[3\]\{\-3~3\} (540|80a) @ <binary>!wmain"]),
        (FULL,    [ 4, -4, 4], [r"OOBW\[4n\]\{\-4n~4n\} (540|80a) @ <binary>!wmain"]),
        (FULL,    [ 5, -5, 5], [r"OOBW\[4n\+1\]\{-4n\-1~4n\+1\} (540|80a) @ <binary>!wmain"]),
        (FULL,    [ 1, -4, 5], [r"OOBW\[1\]\{\-4n~4n\} (540|80a) @ <binary>!wmain"]), # Last byte written is within bounds!
        # Make sure very large allocations do not cause issues in cBugId
        (FULL,    [uLargeHeapBlockSize, -4, 4], [r"OOBW\[4n\]\{\-4n~4n\} (540|80a) @ <binary>!wmain"]),
      ],
    },
  };
