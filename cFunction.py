class cFunction(object):
  def __init__(oSelf, oModule, sSymbol):
    oSelf.oModule = oModule;
    oSelf.sSymbol = sSymbol;
    oSelf.sCdbId = "%s!%s" % (oModule.sCdbId, oSelf.sSymbol);
    oSelf.sName = "%s!%s" % (oModule.sBinaryName, oSelf.sSymbol);
    # Replace complex template stuff with "<...>" to make a symbol easier to read.
    asComponents = [""];
    for sChar in sSymbol:
      if sChar == "<":
        asComponents.append("");
      elif sChar == ">":
        if len(asComponents) == 1:
          asComponents[-1] += ">"; # this is not closing a "<".
        else:
          sTemplate = asComponents.pop(); # discard contents of template
          asComponents[-1] += "<...>";
      else:
        asComponents[-1] += sChar;
    oSelf.sSimpifiedSymbol = "<".join(asComponents);
    oSelf.sSimplifiedName = "%s!%s" % (oModule.sSimplifiedName, oSelf.sSimpifiedSymbol);
    oSelf.sUniqueName = sSymbol;
