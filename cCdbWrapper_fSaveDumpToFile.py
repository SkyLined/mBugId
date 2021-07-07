from mNotProvided import *;

def cCdbWrapper_fSaveDumpToFile(oCdbWrapper, sFilePath, bOverwrite, bFull):
  fAssertType("sFilePath", sFilePath, str);
  asbFlags = [s for s in [
    b"/o" if bOverwrite else None,
    b"/mAfFhuty" if bFull else b"/miR",
  ] if s];
  oCdbWrapper.fasbExecuteCdbCommand( \
    sbCommand = b".dump %s \"%s\";" % (b" ".join(asbFlags), bytes(sFilePath, 'latin1')),
    sb0Comment = b"Save dump to file",
  );
