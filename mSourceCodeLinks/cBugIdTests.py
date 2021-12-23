from .cSourceCodeLink import cSourceCodeLink;

aoSourceCodeLinks = [
  cSourceCodeLink( # Blink
    srbPathHeader = rb"\w+:(\\\w+)*\\cBugId\\tests\\src\\",
    sbFileOnlyURLTemplate = b"https://github.com/SkyLined/cBugId/tree/master/Tests/src/%(path)s",
    sbFileAndLineNumberURLTemplate = b"https://github.com/SkyLined/cBugId/tree/master/Tests/src/%(path)s#L%(line_number)s",
  ),
];