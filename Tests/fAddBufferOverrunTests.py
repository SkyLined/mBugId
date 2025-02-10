from mTestLevels import NORMAL, FULL;

nExpectedTestTimeOnX64 = 2;

def fAddBufferOverrunTests(dxTests):
  dxTests["BufferOverrun"] = {
    "Heap": {
      "Read": [
        # These issues are not detected until they cause an access violation. Heap blocks
        # may be aligned up to 0x10 bytes.
        (NORMAL, [0xC, 5], [r"OOBR\[4n\]\+4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],                 nExpectedTestTimeOnX64),
        (FULL,   [0xD, 5], [r"OOBR\[4n\+1\]\+3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte",
                            r"OOBR\[4n\+1\]\+4n (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],              nExpectedTestTimeOnX64),
        (FULL,   [0xE, 5], [r"OOBR\[4n\+2\]\+2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte",
                            r"OOBR\[4n\+2\]\+3 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],               nExpectedTestTimeOnX64),
        (FULL,   [0xF, 5], [r"OOBR\[4n\+3\]\+1 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte",
                            r"OOBR\[4n\+3\]\+2 (3ae\.540|3f0\.80a) @ <binary>!fuReadByte"],               nExpectedTestTimeOnX64),
      ],
      "Write": [
        # These issues are detected when they cause an access violation, but earlier
        # OOBW-s took place that did not cause AVs. This causes memory corruption, which
        # is detected and reported in the bug id between curly braces. This next test
        # causes one AV, which is reported first. Then when collateral continues and the
        # application frees the memory, verifier.dll notices the corruption and reports
        # it as well...
        
        # The first bug is triggered when there is an AV caused by the process writing byte #5
        # beyond the page allocated for the heap block. The second bug happens when the heap
        # memory is freed and the heap corruption triggered by bytes #1-4 is detected.
        (NORMAL, [ 0xC, 5], [r"BOF\[4n\]\+4n\{\+0~4n\} (975\.540|113\.80a) @ <binary>!fWriteByte",
                              r"BOF\[4n\]\{\+0~4n\} (540|80a) @ <binary>!wmain"],                         nExpectedTestTimeOnX64),
        # These tests cause multiple AVs as the buffer overflow continues to write
        # beyond the end of the buffer. The first one is detect as a BOF, as the AV
        # is sequential to the heap corruption in the heap block suffix that we can
        # detect. The second AV is sequential to the first, but we do not track that
        # and since it is not sequential to the existing heap corruption, it is not
        # reported as a BOF but rather as an OOBW.
        (FULL,   [ 0xD, 5], [r"BOF\[4n\+1\]\+3\{\+0~3\} (975\.540|113\.80a) @ <binary>!fWriteByte",
                              r"OOBW\[4n\+1\]\+4n\{\+0~3\} (975\.540|113\.80a) @ <binary>!fWriteByte"],   nExpectedTestTimeOnX64),
        (FULL,   [ 0xE, 5], [r"BOF\[4n\+2\]\+2\{\+0~2\} (975\.540|113\.80a) @ <binary>!fWriteByte",
                              r"OOBW\[4n\+2\]\+3\{\+0~2\} (975\.540|113\.80a) @ <binary>!fWriteByte"],    nExpectedTestTimeOnX64),
        (FULL,   [ 0xF, 5], [r"BOF\[4n\+3\]\+1\{\+0~1\} (975\.540|113\.80a) @ <binary>!fWriteByte",
                              r"OOBW\[4n\+3\]\+2\{\+0~1\} (975\.540|113\.80a) @ <binary>!fWriteByte"],    nExpectedTestTimeOnX64),
        # For this buffer overflow, there is no heap block suffix in which to detect corruption, so it cannot be
        # detected as a BOF.
        (FULL,   [0x10, 5], [r"OOBW\[4n\]\+0 (975\.540|113\.80a) @ <binary>!fWriteByte",
                              r"OOBW\[4n\]\+1 (975\.540|113\.80a) @ <binary>!fWriteByte"],                nExpectedTestTimeOnX64),
      ],
    },
    "Stack": {
      "Write": [
        # Stack based heap overflows can cause an access violation if the run off the
        # end of the stack, or a debug break when they overwrite the stack cookie and
        # the function returns. Finding out how much to write to overwrite the stack
        # cookie but not run off the end of the stack requires a bit of trial and error.
        # It seems allocating 0x10 bytes and writing 0x200 does the trick on x86 and x64.
        (NORMAL, [0x10, 0x200], [r"OOBW:Stack (540|80a) @ <binary>!wmain"],                               nExpectedTestTimeOnX64),
        # The OS does not allocate a guard page at the top of the stack. Subsequently,
        # there may be a writable allocation there, and a large enough stack overflow
        # will write way past the end of the stack before causing an AV. This causes a
        # different BugId, so this test does not produce a reliable BugId at the moment.
        # TODO: Reimplement page heap and add feature that adds guard pages to all
        # virtual allocations, so stacks buffer overflows are detected as soon as they
        # read/write past the end of the stack.
        # (NORMAL, [0x10, 0x100000], [r"AVW\[Stack\]\+0 (975\.540|113\.80a) @ <binary>!fWriteByte"],      nExpectedTestTimeOnX64),
      ],
    },
  };
