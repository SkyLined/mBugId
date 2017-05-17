import re;

def cCdbWrapper_fuGetValueForSymbol(oCdbWrapper, sValue):
  # Symbols can contain chars that cause syntax errors, so some escaping may be needed using @!"symbol"+offset.
  # The offset must be outside the escaped string because a symbol that is just a module+offset can cause a
  # "Numeric expression missing from '@!"module+offset"'" error, whereas @!"module"+offset works fine.
  oSymbolAndOffsetMatch = re.match(r"^(.+?)(\+(?:0x)?[0-9a-f]+)?$", sValue);
  assert oSymbolAndOffsetMatch, "Unrecognized symbol pattern: %s" % sValue;
  sSymbol, sOffset = oSymbolAndOffsetMatch.groups();
  return oCdbWrapper.fuGetValue('@!"%s"%s' % (sSymbol, sOffset or ""), "get address for symbol");
