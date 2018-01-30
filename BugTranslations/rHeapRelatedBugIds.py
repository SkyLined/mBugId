import re;

rHeapRelatedBugIds = re.compile(r"^(%s)(\[\d.*|@\w+)?$" % "|".join([
  "AV[RWE]",
  "BOF",
  "DoubleFree",
  "HeapCorrupt",
  "MisalignedFree",
  "OOB[RWE]",
  "OOB[RWE]AF",
  "OOM",
  "[RWE]AF",
  "UnknownVerifierError",
  "WrongHeap",
]));