from mNotProvided import *;

from ..mCP437 import fsCP437FromBytesString;

def cCdbWrapper_fSaveDumpToFile(oCdbWrapper, sFilePath, bOverwrite, bFull):
  fAssertType("sFilePath", sFilePath, str);
  asbFlags = [s for s in [
    b"/o" if bOverwrite else None,
    b"/mAfFhuty" if bFull else b"/miR",
  ] if s];
  oCdbWrapper.fasbExecuteCdbCommand( \
    sbCommand = b".dump %s \"%s\";" % (b" ".join(asbFlags), bytes(sFilePath, "ascii", "strict")),
    sb0Comment = b"Save dump to file",
  );
