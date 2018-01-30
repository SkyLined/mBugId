import re;

rHeapRelatedBugIds = re.compile(r"^(%s)(\[\d.*|@\w+)?$" % "|".join([
  "AV[RWE]",
  "BOF",
  "DoubleFree",
  "HeapCorrupt",
  "IncorrectHeap",
  "MisalignedFree",
  "OOB[RWE]",
  "OOBUAF[RWE]",
  "OOM",
  "UAF[RWE]",
  "UnknownVerifierError",
]));