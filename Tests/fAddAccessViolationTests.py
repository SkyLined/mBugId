from mBugId.mAccessViolation.fbUpdateReportForSpecialPointer import gddtsDetails_uSpecialAddress_sISA;

from mTestLevels import NORMAL, x64, FULL, FULL_x86, FULL_x64;

def fAddAccessViolationTests(dxTests):
  dxAccessViolationTests = dxTests["AccessViolation"] = {
    "Read": [
      # NULL pointer,
      (NORMAL,   [1],                   [r"AVR:NULL\+1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [2],                   [r"AVR:NULL\+2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [3],                   [r"AVR:NULL\+3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [4],                   [r"AVR:NULL\+4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [5],                   [r"AVR:NULL\+4n\+1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (NORMAL,   [-1],                  [r"AVR:NULL\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [-2],                  [r"AVR:NULL\-2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [-3],                  [r"AVR:NULL\-3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [-4],                  [r"AVR:NULL\-4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [-5],                  [r"AVR:NULL\-4n\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [-0x11],               [r"AVR:NULL\-4n\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [-0x101],              [r"AVR:NULL\-4n\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     [-0x1001],             [r"AVR:NULL\-4n\-1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (NORMAL,   ["Unallocated"],       [r"AVR:Unallocated (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     ["NoAccess"],          [r"AVR:NoAccess\[4n\]@0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     ["Reserved"],          [r"AVR:Reserved\[4n\]@0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL,     ["Guard"],             [r"AVR:Guard\[4n\]@0 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL_x64, [    0x7fffffff0000],  [r"AVR:Invalid (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL_x64, [    0x7fffffffffff],  [r"AVR:Invalid (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (x64,      [    0x800000000000],  [r"AVR:Invalid (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVR:Invalid (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
      (FULL_x64, [0xffff800000000000],  [r"AVR:Invalid (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"]),
    ],
    "Write": [
      (FULL,     [1],                   [r"AVW:NULL\+1 (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL,     [-1],                  [r"AVW:NULL\-1 (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL,     ["Unallocated"],       [r"AVW:Unallocated (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (NORMAL,   ["NoAccess"],          [r"AVW:NoAccess\[4n\]@0 (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL,     ["Reserved"],          [r"AVW:Reserved\[4n\]@0 (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL,     ["Guard"],             [r"AVW:Guard\[4n\]@0 (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL_x64, [    0x7fffffff0000],  [r"AVW:Invalid (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL_x64, [    0x7fffffffffff],  [r"AVW:Invalid (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (x64,      [    0x800000000000],  [r"AVW:Invalid (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVW:Invalid (975\.540|113\.80a) @ <binary>!fWriteByte"]),
      (FULL_x64, [0xffff800000000000],  [r"AVW:Invalid (975\.540|113\.80a) @ <binary>!fWriteByte"]),
    ],
    "Call": [
      # For unknown reasons the stack differs between x86 and x64 and can even be truncated.
      # TODO: findout why and fix it.
      (FULL,     [1],                   [r"AVE:NULL\+1 (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL,     [-1],                  [r"AVE:NULL\-1 (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL,     ["Unallocated"],       [r"AVE:Unallocated (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL,     ["NoAccess"],          [r"AVE:NoAccess\[4n\]@0 (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL,     ["Reserved"],          [r"AVE:Reserved\[4n\]@0 (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (NORMAL,   ["Guard"],             [r"AVE:Guard\[4n\]@0 (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL_x64, [    0x7fffffff0000],  [r"AVE:Invalid (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL_x64, [    0x7fffffffffff],  [r"AVE:Invalid (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (x64,      [    0x800000000000],  [r"AVE:Invalid (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVE:Invalid (b2d\.540|681\.80a) @ <binary>!fCall"]),
      (FULL_x64, [0xffff800000000000],  [r"AVE:Invalid (b2d\.540|681\.80a) @ <binary>!fCall"]),
    ],
    "Jump": [
      (FULL,     [1],                   [r"AVE:NULL\+1 (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL,     [-1],                  [r"AVE:NULL\-1 (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL,     ["Unallocated"],       [r"AVE:Unallocated (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL,     ["NoAccess"],          [r"AVE:NoAccess\[4n\]@0 (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (NORMAL,   ["Reserved"],          [r"AVE:Reserved\[4n\]@0 (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL,     ["Guard"],             [r"AVE:Guard\[4n\]@0 (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL_x64, [    0x7fffffff0000],  [r"AVE:Invalid (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL_x64, [    0x7fffffffffff],  [r"AVE:Invalid (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (x64,      [    0x800000000000],  [r"AVE:Invalid (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVE:Invalid (414\.540|fb0\.80a) @ <binary>!fJump"]),
      (FULL_x64, [0xffff800000000000],  [r"AVE:Invalid (414\.540|fb0\.80a) @ <binary>!fJump"]),
    ],
  };
  # There is a large number of special addresses that we detect.
  # We want to test each one, and we want to make sure we can detect them
  # with each access type. Exhaustively doing so takes a very long time.
  # We will cut some corners and pick a different access type for each
  # special address so we cover various combinations both of them without
  # trying each and every combination. This should give decent test coverage.
  ttsAccessType_and_srBugIdFormatString = (
    ("Read", r"AVR:%s (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"),
    ("Write", r"AVW:%s (975\.540|113\.80a) @ <binary>!fWriteByte"),
    ("Call", r"AVE:%s (b2d\.540|681\.80a) @ <binary>!fCall"),
    ("Jump", r"AVE:%s (414\.540|fb0\.80a) @ <binary>!fJump"),
  );
  uAccessTypeIndex = 0;
  for (sISA, dtsDetails_uSpecialAddress) in gddtsDetails_uSpecialAddress_sISA.items():
    uTestLevel = FULL_x86 if sISA == "x86" else FULL_x64;
    for (uSpecialAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
      (sAccessType, srBugIdFormatString) = ttsAccessType_and_srBugIdFormatString[uAccessTypeIndex];
      uAccessTypeIndex = (uAccessTypeIndex + 1) % len(ttsAccessType_and_srBugIdFormatString);
      dxAccessViolationTests[sAccessType].append(
        (uTestLevel, [uSpecialAddress], [srBugIdFormatString % sAddressId]),
      );
  # Two additional tests using the last special address to make sure offsets from these addresses
  # are handled correctly:
  dxAccessViolationTests["Read"] += [
    (uTestLevel, [uSpecialAddress + 5], [r"AVR:%s\+4n\+1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte" % sAddressId]),
    (uTestLevel, [uSpecialAddress - 6], [r"AVR:%s\-4n\-2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte" % sAddressId]),
  ];
