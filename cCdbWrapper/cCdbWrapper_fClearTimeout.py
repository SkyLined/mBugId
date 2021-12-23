def cCdbWrapper_fClearTimeout(oCdbWrapper, oTimeout):
  try:
    oCdbWrapper.aoTimeouts.remove(oTimeout);
  except ValueError:
    pass; # It has already been cleared or fired.