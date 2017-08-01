import re;

def fsCleanCdbSymbolWithOffset(sSymbolWithOffset):
  # Symbols can contain chars that cause syntax errors, so some escaping may be needed using @!"symbol"+offset.
  # The offset must be outside the escaped string because a symbol that is just a module+offset can cause a
  # "Numeric expression missing from '@!"module+offset"'" error, whereas @!"module"+offset works fine.
  oSymbolAndOffsetMatch = re.match(r"^(.+?)(\+(?:0x)?[0-9a-f]+)?$", sSymbolWithOffset);
  assert oSymbolAndOffsetMatch, "Unrecognized value: %s" % sSymbolWithOffset;
  sSymbol, sOffset = oSymbolAndOffsetMatch.groups();
  return '@!"%s"%s' % (sSymbol, sOffset or "");
