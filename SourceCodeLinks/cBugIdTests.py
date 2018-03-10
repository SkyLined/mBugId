from .cSourceCodeLink import cSourceCodeLink;

aoSourceCodeLinks = [
  cSourceCodeLink( # Blink
    srPathHeader = r"\w+:(\\\w+)*\\cBugId\\tests\\src\\",
    sFileOnlyURLTemplate = "https://github.com/SkyLined/cBugId/tree/master/Tests/src/%(path)s",
    sFileAndLineNumberURLTemplate = "https://github.com/SkyLined/cBugId/tree/master/Tests/src/%(path)s#L%(line_number)s",
  ),
];