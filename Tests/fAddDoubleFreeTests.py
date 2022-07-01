from mTestLevels import NORMAL, FULL;

def fAddDoubleFreeTests(dxTests, uMaxMemoryDumpSize):
  dxTests["DoubleFree"] = [
    (NORMAL,  [       1], [r"DoubleFree\[1\] (540|80a) @ <binary>!wmain"]),
    (FULL,    [       2], [r"DoubleFree\[2\] (540|80a) @ <binary>!wmain"]),
    (FULL,    [       3], [r"DoubleFree\[3\] (540|80a) @ <binary>!wmain"]),
    (FULL,    [       4], [r"DoubleFree\[4n\] (540|80a) @ <binary>!wmain"]),
    # Extra tests to check if the code deals correctly with memory areas too large to dump completely:
    # (Note that these blocks will be large, which cause the memory to actually be freed. If this
    # happens, information about the block's size if destroedy and BugId shows "[?]" in the bug id)
    (FULL,    [uMaxMemoryDumpSize],     [r"DoubleFree\[(4n|\?)\] (540|80a) @ <binary>!wmain"]),
    (FULL,    [uMaxMemoryDumpSize + 1], [r"DoubleFree\[(4n\+1|\?)\] (540|80a) @ <binary>!wmain"]),
    (FULL,    [uMaxMemoryDumpSize + 4], [r"DoubleFree\[(4n|\?)\] (540|80a) @ <binary>!wmain"]),
  ];
