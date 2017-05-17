from cSourceCodeLink import cSourceCodeLink;

srBasePath = r"\w+:(\\\w+)*\\(build\\slave\\win-asan\\build|build\\slave\\syzygy_official\\build|win(64)?_pgo)";

aoSourceCodeLinks = [
  cSourceCodeLink( # Blink
    srPathHeader = srBasePath + r"\\src\\third_party\\webkit\\",
    sURLTemplate = "https://chromium.googlesource.com/chromium/blink/+/master/%(path)s#%(line_number)s",
  ),
  cSourceCodeLink( # V8
    srPathHeader = srBasePath + r"\\src\\v8\\",
    sURLTemplate = "https://chromium.googlesource.com/v8/v8.git/+/master/%(path)s#%(line_number)s",
  ),
  cSourceCodeLink( # syzygy
    srPathHeader = srBasePath + r"\\src\\syzygy\\",
    sURLTemplate = "https://github.com/google/syzygy/blob/master/syzygy/%(path)s#L%(line_number)s",
  ),
  cSourceCodeLink( # base
    srPathHeader = srBasePath + r"\\src\\base\\",
    sURLTemplate = "https://chromium.googlesource.com/chromium/src/base/+/master/%(path)s#%(line_number)s",
  ),
  cSourceCodeLink( # content
    srPathHeader = srBasePath + r"\\src\\content\\",
    sURLTemplate = "https://chromium.googlesource.com/chromium/chromium/+/master/content/%(path)s#%(line_number)s",
  ),
];