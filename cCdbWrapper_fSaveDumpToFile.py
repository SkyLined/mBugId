def cCdbWrapper_fSaveDumpToFile(oCdbWrapper, sFilePath, bOverwrite, bFull):
  assert isinstance(sFilePath, str), \
      "sFilePath must be a string, not %s" % repr(sFilePath);
  asFlags = [s for s in [
    "/o" if bOverwrite else None,
    "/f" if bFull else "/ma",
  ] if s];
  oCdbWrapper.fasExecuteCdbCommand( \
    sCommand = ".dump %s \"%s\";" % (" ".join(asFlags), sFilePath),
    sComment = "Save dump to file",
  );
