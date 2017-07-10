from cSourceCodeLink import cSourceCodeLink;

srBasePath = r"\w+:(\\\w+)*\\(%s)\\src" % "|".join([
  r"build\\slave\\(win-asan|syzygy_official|win_upload_clang)\\build",
  r"win_asan_release",
  r"win(64)?_pgo",
]);

aoSourceCodeLinks = [
  cSourceCodeLink( # Blink
    srPathHeader = srBasePath + r"\\third_party\\webkit\\source\\",
    sURLTemplate = "https://chromium.googlesource.com/chromium/src/+/master/third_party/WebKit/Source/%(path)s#%(line_number)s",
  ),
  cSourceCodeLink( # syzygy
    srPathHeader = srBasePath + r"\\syzygy\\",
    sURLTemplate = "https://github.com/google/syzygy/blob/master/syzygy/%(path)s#L%(line_number)s",
  ),
  cSourceCodeLink( # V8
    srPathHeader = srBasePath + r"\\v8\\",
    sURLTemplate = "https://chromium.googlesource.com/v8/v8.git/+/master/%(path)s#%(line_number)s",
  ),
  cSourceCodeLink( # ASan/LLVM
    srPathHeader = srBasePath + r"\\third_party\\llvm\projects\\compiler-rt\\",
    sURLTemplate = "https://github.com/llvm-mirror/compiler-rt/tree/master/%(path)s#L%(line_number)s",
  ),
  # Anything else is assumed to be part of chromium. This is very likely not correct, as there are bound to be more
  # exceptions, so please report if you find any!
  # It is correct for the following folders: content, ipc, (list is not yet exhaustive).
  cSourceCodeLink(
    srPathHeader = srBasePath,
    sURLTemplate = "https://chromium.googlesource.com/chromium/src/+/master/%(path)s#%(line_number)s",
  ),
];