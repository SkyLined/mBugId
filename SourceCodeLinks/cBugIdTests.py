from cSourceCodeLink import cSourceCodeLink;

aoSourceCodeLinks = [
  cSourceCodeLink( # Blink
    srPathHeader = r"\w+:(\\\w+)*\\cBugId\\tests\\src\\",
    sURLTemplate = "https://github.com/SkyLined/cBugId/tree/master/Tests/src/%(path)s#L%(line_number)s",
  ),
];