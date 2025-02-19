from mTestLevels import NORMAL, FULL;

nExpectedTestTimeOnX64 = 2;

def fAddOutOfBoundsTests(dxTests, uLargeHeapBlockSize):
  # Small out-of-bounds writes that do not go outside of the memory page and therefore do not cause access violations.
  # These are detected by Page Heap / Application Verifier when the memory is freed.
  # This means it is not reported in the `fWriteByte` function that does the writing,
  # but in the `fFreeAllocatedHeapMemory` function that frees the memory.
  srFreeIdAndLocation = r"3b0\.f3d @ <binary>!fFreeAllocatedHeapMemory";
  dxTests["OutOfBounds"] = {
    "Heap": {
      "Write": [
        (NORMAL,  [ 1, -1, 1], [r"OOBW\[1\]\{\-1~1\} " + srFreeIdAndLocation],               nExpectedTestTimeOnX64),
        (FULL,    [ 2, -2, 2], [r"OOBW\[2\]\{\-2~2\} " + srFreeIdAndLocation],               nExpectedTestTimeOnX64),
        (FULL,    [ 3, -3, 3], [r"OOBW\[3\]\{\-3~3\} " + srFreeIdAndLocation],               nExpectedTestTimeOnX64),
        (FULL,    [ 4, -4, 4], [r"OOBW\[4n\]\{\-4n~4n\} " + srFreeIdAndLocation],            nExpectedTestTimeOnX64),
        (FULL,    [ 5, -5, 5], [r"OOBW\[4n\+1\]\{-4n\-1~4n\+1\} " + srFreeIdAndLocation],    nExpectedTestTimeOnX64),
        (FULL,    [ 1, -4, 5], [r"OOBW\[1\]\{\-4n~4n\} " + srFreeIdAndLocation],             nExpectedTestTimeOnX64), # Last byte written is within bounds!
        (FULL,    [ 4, -4, 1], [r"OOBW\[4n\]\{\-4n~1\} " + srFreeIdAndLocation],             nExpectedTestTimeOnX64),
        # Make sure very large allocations do not cause issues in cBugId
        (FULL,    [uLargeHeapBlockSize, -4, 4],
                               [r"OOBW\[4n\]\{\-4n~4n\} " + srFreeIdAndLocation],            nExpectedTestTimeOnX64),
      ],
    },
  };
