from mBugId.mAccessViolation.fbUpdateReportForSpecialPointer import gddtsDetails_uSpecialAddress_sISA;

from mTestLevels import NORMAL, x86, x64, FULL, FULL_x86, FULL_x64;

nExpectedTestTimeOnX64 = 2;

def fAddCorruptStackPointerTests(dxTests):
  # For all of these we have to assume that the stack may be corrupt, so only
  # one valid frame might be detected, hence additional frames ids should be
  # optional:
  srPopIdAndLocation = r"377(\.5b3)? @ <binary>!fPopWithStackPointer";
  srPushIdAndLocation = r"5cd(\.5b3)? @ <binary>!fPushWithStackPointer";
  srCallIdAndLocation = r"db0(\.5b3)? @ <binary>!fCallWithStackPointer";
  srRetIdAndLocation = r"2a6(\.5b3)? @ <binary>!fRetWithStackPointer";
  # After a CALL with an invalid stack pointer, BugId will use a poison value
  # which ends up in the instruction pointer and results in one of these BugIds:
  # Weirdly, the exact BugId seems to vary between runs of the same test. TODO:
  # find out why and try to return a single BugId.
  srExecPoison = r"AVE:Poison\+0 (XXX @ <binary>!\(unknown\)|db0.5b3 @ <binary>!fCallWithStackPointer)";
  dxCorruptStackPointerTests = dxTests["CorruptStackPointer"] = {
    "Pop": [
      # NULL pointer,
      (NORMAL,   [1],                   [r"AVR:NULL\+1 " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [2],                   [r"AVR:NULL\+2 " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [3],                   [r"AVR:NULL\+3 " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [4],                   [r"AVR:NULL\+4n " + srPopIdAndLocation],        nExpectedTestTimeOnX64),
      (FULL,     [5],                   [r"AVR:NULL\+4n\+1 " + srPopIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   [-1],                  [r"AVR:NULL\-1 " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [-2],                  [r"AVR:NULL\-2 " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [-3],                  [r"AVR:NULL\-3 " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     [-4],                  [r"AVR:NULL\-4n " + srPopIdAndLocation],        nExpectedTestTimeOnX64),
      (FULL,     [-5],                  [r"AVR:NULL\-4n\-1 " + srPopIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     [-0x11],               [r"AVR:NULL\-4n\-1 " + srPopIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     [-0x101],              [r"AVR:NULL\-4n\-1 " + srPopIdAndLocation],     nExpectedTestTimeOnX64),
      (FULL,     [-0x1001],             [r"AVR:NULL\-4n\-1 " + srPopIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   ["Unallocated"],       [r"AVR:Unallocated " + srPopIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   ["NoAccess"],          [r"AVR:NoAccess\[4n\]@0 " + srPopIdAndLocation],nExpectedTestTimeOnX64),
      (NORMAL,   ["Reserved"],          [r"AVR:Reserved\[4n\]@0 " + srPopIdAndLocation],nExpectedTestTimeOnX64),
      (NORMAL,   ["GuardPage"],         [r"AVR:Guard\[4n\]@0 " + srPopIdAndLocation],   nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVR:Invalid " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVR:Invalid " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVR:Invalid " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVR:Invalid " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVR:Invalid " + srPopIdAndLocation],         nExpectedTestTimeOnX64),
    ],
    "Push": [
      (NORMAL,   [1],                   [r"AVW:NULL\+1 " + srPushIdAndLocation],         nExpectedTestTimeOnX64),
      (NORMAL,   [-1],                  [r"AVW:NULL\-1 " + srPushIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL,     ["Unallocated"],       [r"AVW:Unallocated " + srPushIdAndLocation],     nExpectedTestTimeOnX64),
      (NORMAL,   ["NoAccess"],          [r"AVW:NoAccess\[4n\]@0 " + srPushIdAndLocation],nExpectedTestTimeOnX64),
      (NORMAL,   ["Reserved"],          [r"AVW:Reserved\[4n\]@0 " + srPushIdAndLocation],nExpectedTestTimeOnX64),
      (NORMAL,   ["GuardPage"],         [r"AVW:Guard\[4n\]@0 " + srPushIdAndLocation],   nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVW:Invalid " + srPushIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVW:Invalid " + srPushIdAndLocation],         nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVW:Invalid " + srPushIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVW:Invalid " + srPushIdAndLocation],         nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVW:Invalid " + srPushIdAndLocation],         nExpectedTestTimeOnX64),
    ],
    "Call": [
      (NORMAL,   [1],                   [r"AVW:NULL\+1 " + srCallIdAndLocation],                          nExpectedTestTimeOnX64),
      (NORMAL,   [-1],                  [r"AVW:NULL\-1 " + srCallIdAndLocation],                          nExpectedTestTimeOnX64),
      (FULL,     ["Unallocated"],       [r"AVW:Unallocated " + srCallIdAndLocation,       srExecPoison],  nExpectedTestTimeOnX64),
      (NORMAL,   ["NoAccess"],          [r"AVW:NoAccess\[4n\]@0 " + srCallIdAndLocation],                 nExpectedTestTimeOnX64),
      (NORMAL,   ["Reserved"],          [r"AVW:Reserved\[4n\]@0 " + srCallIdAndLocation,  srExecPoison],  nExpectedTestTimeOnX64),
      (NORMAL,   ["GuardPage"],         [r"AVW:Guard\[4n\]@0 " + srCallIdAndLocation],                    nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVW:Invalid " + srCallIdAndLocation,           srExecPoison],  nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVW:Invalid " + srCallIdAndLocation,           srExecPoison],  nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVW:Invalid " + srCallIdAndLocation,           srExecPoison],  nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVW:Invalid " + srCallIdAndLocation,           srExecPoison],  nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVW:Invalid " + srCallIdAndLocation,           srExecPoison],  nExpectedTestTimeOnX64),
    ],
    "Ret": [
      (NORMAL,   [1],                   [r"AVR:NULL\+1 " + srRetIdAndLocation],                            nExpectedTestTimeOnX64),
      (NORMAL,   [-1],                  [r"AVR:NULL\-1 " + srRetIdAndLocation],                            nExpectedTestTimeOnX64),
      (FULL,     ["Unallocated"],       [r"AVR:Unallocated " + srRetIdAndLocation,         srExecPoison],  nExpectedTestTimeOnX64),
      (NORMAL,   ["NoAccess"],          [r"AVR:NoAccess\[4n\]@0 " + srRetIdAndLocation],                   nExpectedTestTimeOnX64),
      (NORMAL,   ["Reserved"],          [r"AVR:Reserved\[4n\]@0 " + srRetIdAndLocation,    srExecPoison],  nExpectedTestTimeOnX64),
      (NORMAL,   ["GuardPage"],         [r"AVR:Guard\[4n\]@0 " + srRetIdAndLocation],                      nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffff0000],  [r"AVR:Invalid " + srRetIdAndLocation,             srExecPoison],  nExpectedTestTimeOnX64),
      (FULL_x64, [    0x7fffffffffff],  [r"AVR:Invalid " + srRetIdAndLocation,             srExecPoison],  nExpectedTestTimeOnX64),
      (x64,      [    0x800000000000],  [r"AVR:Invalid " + srRetIdAndLocation,             srExecPoison],  nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff7fffffffffff],  [r"AVR:Invalid " + srRetIdAndLocation,             srExecPoison],  nExpectedTestTimeOnX64),
      (FULL_x64, [0xffff800000000000],  [r"AVR:Invalid " + srRetIdAndLocation,             srExecPoison],  nExpectedTestTimeOnX64),
    ],
  };
  # There is a large number of special addresses that we detect.
  # We want to test each one, and we want to make sure we can detect them
  # with each access type. Exhaustively doing so takes a very long time.
  # We will cut some corners and pick a different access type for each
  # special address so we cover various combinations both of them without
  # trying each and every combination. This should give decent test coverage.
  ttsAccessType_and_srBugIdFormatString = (
    ("Pop", r"AVR:%s " + srPopIdAndLocation),
    ("Push", r"AVW:%s " + srPushIdAndLocation),
    ("Call", r"AVW:%s " + srCallIdAndLocation),
    ("Ret", r"AVR:%s " + srRetIdAndLocation),
  );
  uAccessTypeIndex = 0;
  for (sISA, dtsDetails_uSpecialAddress) in gddtsDetails_uSpecialAddress_sISA.items():
    uTestLevel = FULL_x86 if sISA == "x86" else FULL_x64;
    for (uSpecialAddress, (sAddressId, sAddressDescription, sSecurityImpact)) in dtsDetails_uSpecialAddress.items():
      (sAccessType, srBugIdFormatString) = ttsAccessType_and_srBugIdFormatString[uAccessTypeIndex];
      uAccessTypeIndex = (uAccessTypeIndex + 1) % len(ttsAccessType_and_srBugIdFormatString);
      asExpectedBugIds = [srBugIdFormatString % sAddressId];
      if sAccessType in ["Call", "Ret"]:
        # Collateral bug handling will result in a poisoned instruction pointer:
        asExpectedBugIds.append(srExecPoison);
      else:
        continue;
      dxCorruptStackPointerTests[sAccessType].append(
        (uTestLevel, [uSpecialAddress], asExpectedBugIds,         nExpectedTestTimeOnX64),
      );
  # Two additional tests using the last special address to make sure offsets from these addresses
  # are handled correctly:
  dxCorruptStackPointerTests["Pop"] += [
    (uTestLevel, [uSpecialAddress + 5], [r"AVR:%s\+4n\+1 %s" % (sAddressId, srPopIdAndLocation)], nExpectedTestTimeOnX64),
    (uTestLevel, [uSpecialAddress - 6], [r"AVR:%s\-4n\-2 %s" % (sAddressId, srPopIdAndLocation)], nExpectedTestTimeOnX64),
  ];