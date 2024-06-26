class cFunction(object):
  def __init__(oSelf, oModule, sbSymbol):
    oSelf.oModule = oModule;
    oSelf.sbSymbol = sbSymbol;
    oSelf.sbCdbId = b"%s!%s" % (oModule.sbCdbId, sbSymbol);
    oSelf.sbName = b"%s!%s" % (oModule.sb0BinaryName or b"<unknown module>", sbSymbol);
    # Replace complex template stuff with "<...>" to make a symbol easier to read.
    asbComponents = [b""];
    for uChar in sbSymbol:
      if uChar == ord("<"):
        asbComponents.append(b"");
      elif uChar == ord(">"):
        if len(asbComponents) == 1:
          asbComponents[-1] += b">"; # this is not closing a "<".
        else:
          sbTemplate = asbComponents.pop(); # discard contents of template
          asbComponents[-1] += b"<...>";
      else:
        asbComponents[-1] += bytes((uChar,));
    oSelf.sbSimpifiedSymbol = b"<".join(asbComponents);
    oSelf.sbSimplifiedName = b"%s!%s" % (oModule.sb0SimplifiedName or b"???", oSelf.sbSimpifiedSymbol);
    oSelf.sbUniqueName = b"%s!%s" % (oModule.sb0UniqueName or b"???", sbSymbol);
