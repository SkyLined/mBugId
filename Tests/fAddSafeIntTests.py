from mTestLevels import FULL, NOT_FULL, FULL_x64;

def fAddSafeIntTests(dxTests):
  dxSafeIntTests = dxTests["SafeInt"] = [
    # A simple list of basic tests is run when not running full tests.
    # When running full tests, a comprehensive quit of tests is run that
    # is generated further down the code...
    (NOT_FULL, ["++", "signed", 64],          [r"IntegerOverflow (540|80a) @ <binary>!wmain"]),
    (NOT_FULL, ["--", "unsigned", 32],        [r"IntegerUnderflow (540|80a) @ <binary>!wmain"]),
    (NOT_FULL, ["*", "signed", 16],           [r"IntegerTruncation (540|80a) @ <binary>!wmain"]),
    (NOT_FULL, ["truncate", "signed", 8],     [r"IntegerTruncation (540|80a) @ <binary>!wmain"]),
    (NOT_FULL, ["signedness", "signed", 16],  [r"IntegerTruncation (540|80a) @ <binary>!wmain"]),
  ];

  for (sOperation, sBugTypeId) in {
    "++": "IntegerOverflow",
    "--": "IntegerUnderflow",
    "*": "IntegerTruncation",
    "truncate": "IntegerTruncation",
    "signedness": "IntegerTruncation",
  }.items():
    for sSignedness in ["signed", "unsigned"]:
      for uBits in [8, 16, 32, 64]:
        if sOperation == "truncate" and (sSignedness == "unsigned" or uBits == 64):
          # * The signedness argument is ignored for "truncate", so we only need to run
          #   the test once. We do so for "signed" and skip "unsigned".
          # * C++ does not support values > 64 bits, so we cannot truncate a value to
          #   64 bits.
          continue;
        uTestLevel = FULL if uBits < 64 else FULL_x64;
        dxSafeIntTests.append(
          (uTestLevel, [sOperation, sSignedness, uBits], ["%s (540|80a) @ <binary>!wmain" % sBugTypeId])
        );
