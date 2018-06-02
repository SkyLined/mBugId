import re;

rHeapRelatedBugIds = re.compile(r"^(%s)(\[\d.*|\[\?\]|@\w+)?$" % "|".join([
  "AV[RWE!]", # Unspecified Access Violation while Reading/Writing/Executing memory (attempt to r/w/e memory failed)
  "BOF", # Buffer OverFlow (attempt to sequentially write more data to a buffer than the buffer can contain)
  "DoubleFree", # Attempt to free a memory block that has already been freed before.
  "HeapCorrupt", # Unspecified memory corruption detected.
  "MisalignedFree", # Attempt to free memory block using a pointer that does not point to the start of the memory block.
  "OOB[RWE]", # Out-Of-Bounds Read/Write/Execute (attempt to r/w/e outside the bounds of a memory block)
  "OOB[RWE]AF", # Out-Of-Bounds Read/Write/Execute After Free (attempt to r/w/e outside the bounds of a memory block after it has been freed)
  "DEP", # Data execution prevention (attempt to execute non-executable memory)
  "W2RO", # Write to Read-Only memory
  "OOM", # Out Of Memory  (attempt to allocate more memory failed)
  "[RWE]AF", # Read/Write/Execute After Free (attempt to r/w/e memory after it has been freed)
  "UnknownVerifierError", # Unspecified error reported by Application Verifier
  "WrongHeap",  # Attempt to perform an operation on a memory block using the wrong heap handle.
]));