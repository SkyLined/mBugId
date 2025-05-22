from mBugId.mBugReport.mAccessViolation.fbUpdateReportForSpecialPointer import gddtsDetails_uSpecialAddress_sISA;

from mTestLevels import NORMAL, x64, FULL, FULL_x86, FULL_x64;

nExpectedTestTimeOnX64 = 2;

def fAddAccessViolationTests(dxTests):
  srMainIdAndLocation = r"5b3 @ <binary>!wmain";
  srCallIdAndLocation = r"3e6\.5b3 @ <binary>!fCall";
  srJumpIdAndLocation = r"e8c\.5b3 @ <binary>!fJump";
  srPoisonExecIdAndLocation = r"AVE:Poison+0 e8c.5b3 @ bugidtests.exe!fJump";
  dxAccessViolationTests = dxTests["AccessViolation"] = {
    "Read": [
      # NULL pointer,
      (NORMAL,   [1],                   [r"AVR:NULL\+1 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [2],                   [r"AVR:NULL\+2 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [3],                   [r"AVR:NULL\+3 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [4],                   [r"AVR:NULL\+4n " + srMainIdAndLocation],        nExpectedTestTimeOnX64),
      (FULL,     [5],                   [r"AVR:NULL\+4n\+1 " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   [-1],                  [r"AVR:NULL\-1 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [-2],                  [r"AVR:NULL\-2 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [-3],                  [r"AVR:NULL\-3 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [-4],                  [r"AVR:NULL\-4n " + srMainIdAndLocation],        nExpectedTestTimeOnX64),
      (FULL,     [-5],                  [r"AVR:NULL\-4n\-1 " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     [-0x11],               [r"AVR:NULL\-4n\-1 " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     [-0x101],              [r"AVR:NULL\-4n\-1 " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     [-0x1001],             [r"AVR:NULL\-4n\-1 " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   ["Unallocated"],       [r"AVR:Unallocated " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     ["NoAccess"],          [r"AVR:NoAccess\[4n\]@0 " + srMainIdAndLocation],nExpectedTestTimeOnX64),
      (FULL,     ["Reserved"],          [r"AVR:Reserved\[4n\]@0 " + srMainIdAndLocation],nExpectedTestTimeOnX64),
      (FULL,     ["GuardPage"],         [r"AVR:Guard\[4n\]@0 " + srMainIdAndLocation],   nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVR:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVR:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVR:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVR:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVR:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
    ],
    "Write": [
      (FULL,     [1],                   [r"AVW:NULL\+1 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [-1],                  [r"AVW:NULL\-1 " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     ["Unallocated"],       [r"AVW:Unallocated " + srMainIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   ["NoAccess"],          [r"AVW:NoAccess\[4n\]@0 " + srMainIdAndLocation],nExpectedTestTimeOnX64),
      (FULL,     ["Reserved"],          [r"AVW:Reserved\[4n\]@0 " + srMainIdAndLocation],nExpectedTestTimeOnX64),
      (FULL,     ["GuardPage"],         [r"AVW:Guard\[4n\]@0 " + srMainIdAndLocation],   nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVW:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVW:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVW:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVW:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVW:Invalid " + srMainIdAndLocation],         nExpectedTestTimeOnX64),
    ],
    "Call": [
      # For unknown reasons the stack differs between x86 and x64 and can even be truncated.
      # TODO: findout why and fix it.
      (FULL,     [1],                   [r"AVE:NULL\+1 "+ srCallIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL,     [-1],                  [r"AVE:NULL\-1 "+ srCallIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL,     ["Unallocated"],       [r"AVE:Unallocated "+ srCallIdAndLocation],          nExpectedTestTimeOnX64),
      (FULL,     ["NoAccess"],          [r"AVE:NoAccess\[4n\]@0 "+ srCallIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     ["Reserved"],          [r"AVE:Reserved\[4n\]@0 "+ srCallIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   ["GuardPage"],         [r"AVE:Guard\[4n\]@0 "+ srCallIdAndLocation],        nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVE:Invalid "+ srCallIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVE:Invalid "+ srCallIdAndLocation],              nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVE:Invalid "+ srCallIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVE:Invalid "+ srCallIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVE:Invalid "+ srCallIdAndLocation],              nExpectedTestTimeOnX64),
    ],
    "Jump": [
      (FULL,     [1],                   [r"AVE:NULL\+1 "+ srJumpIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL,     [-1],                  [r"AVE:NULL\-1 "+ srJumpIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL,     ["Unallocated"],       [r"AVE:Unallocated "+ srJumpIdAndLocation],          nExpectedTestTimeOnX64),
      (FULL,     ["NoAccess"],          [r"AVE:NoAccess\[4n\]@0 "+ srJumpIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   ["Reserved"],          [r"AVE:Reserved\[4n\]@0 "+ srJumpIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     ["GuardPage"],         [r"AVE:Guard\[4n\]@0 "+ srJumpIdAndLocation],        nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVE:Invalid "+ srJumpIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVE:Invalid "+ srJumpIdAndLocation],              nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVE:Invalid "+ srJumpIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVE:Invalid "+ srJumpIdAndLocation],              nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVE:Invalid "+ srJumpIdAndLocation],              nExpectedTestTimeOnX64),
    ],
  };
  # There is a large number of special addresses that we detect.
  # We want to test each one, and we want to make sure we can detect them
  # with each access type. Exhaustively doing so takes a very long time.
  # We will cut some corners and pick a different access type for each
  # special address so we cover various combinations both of them without
  # trying each and every combination. This should give decent test coverage.
  ttsAccessType_and_srBugIdFormatString = (
    ("Read", r"AVR:%s " + srMainIdAndLocation),
    ("Write", r"AVW:%s " + srMainIdAndLocation),
    ("Call", r"AVE:%s "+ srCallIdAndLocation),
    ("Jump", r"AVE:%s "+ srJumpIdAndLocation),
  );
  uAccessTypeIndex = 0;
  for (sISA, dtsDetails_uSpecialAddress) in gddtsDetails_uSpecialAddress_sISA.items():
    uTestLevel = FULL_x86 if sISA == "x86" else FULL_x64;
    for (uSpecialAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
      (sAccessType, srBugIdFormatString) = ttsAccessType_and_srBugIdFormatString[uAccessTypeIndex];
      uAccessTypeIndex = (uAccessTypeIndex + 1) % len(ttsAccessType_and_srBugIdFormatString);
      dxAccessViolationTests[sAccessType].append(
        (uTestLevel, [uSpecialAddress], [srBugIdFormatString % sAddressId],         nExpectedTestTimeOnX64),
      );
  # Two additional tests using the last special address to make sure offsets from these addresses
  # are handled correctly:
  dxAccessViolationTests["Read"] += [
    (uTestLevel, [uSpecialAddress + 5], [r"AVR:%s\+4n\+1 %s" % (sAddressId, srMainIdAndLocation)], nExpectedTestTimeOnX64),
    (uTestLevel, [uSpecialAddress - 6], [r"AVR:%s\-4n\-2 %s" % (sAddressId, srMainIdAndLocation)], nExpectedTestTimeOnX64),
  ];
